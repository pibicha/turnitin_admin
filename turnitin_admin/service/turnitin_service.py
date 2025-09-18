import logging
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from django.conf import settings
from django.db import transaction

from api.models import WebTurnitinClass, WebAssignments, WebUserAssignments
from .turnitin_web_constants import TurnitinWebConstants
from django.db.models import F
from asgiref.sync import sync_to_async, async_to_sync
from ..settings import DEBUG

logger = logging.getLogger(__name__)

class TurnitinService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': TurnitinWebConstants.USER_AGENT,
            'Accept': TurnitinWebConstants.ACCEPT_HTML
        })
        self.homepage = TurnitinWebConstants.HOMEPAGE
        self.class_name = None
        self.cookies = None

    async def initialize(self):
        """初始化 class_name 和 cookies"""
        self.class_name = await sync_to_async(
            lambda: WebTurnitinClass.objects.get(active_flag='Y').class_name)()
        self.cookies = self.get_cookies()

    def get_cookies(self):
        """获取 Turnitin 的认证 Cookie"""
        if DEBUG:
            return "session-id=0442328f5c024323859b6e736bdc87fc;legacy-session-id=0442328f5c024323859b6e736bdc87fc; path=/; secure; HttpOnly"
        
        try:
            response = self.session.get(
                'http://localhost:8081/admin/api/turnitin/cookie',
                headers={
                    'User-Agent': TurnitinWebConstants.USER_AGENT,
                    'Accept': TurnitinWebConstants.ACCEPT_TEXT
                },
                timeout=600
            )
            response.raise_for_status()
            cookie_str = response.text.strip()
            if not cookie_str or 'session-id' not in cookie_str or 'legacy-session-id' not in cookie_str:
                raise ValueError("无效的 Cookie 格式")
            logger.info(f"成功获取 Cookie: {cookie_str[:50]}...")
            return cookie_str
        except Exception as e:
            logger.error(f"获取 Cookie 失败: {str(e)}")
            raise IOError(f"获取 Cookie 失败: {str(e)}")

    def get_classes(self):
        """获取课程列表"""
        try:
            response = self.session.get(self.homepage, headers={'Cookie': self.cookies}, timeout=600)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            classes = soup.select('td.class_name a')
            return [{
                'title': elem.text.strip(),
                'url': f"https://www.turnitin.com{elem['href']}"
            } for elem in classes if elem.text.strip() == self.class_name]
        except requests.RequestException as e:
            logger.error(f"获取课程失败: {str(e)}")
            raise IOError(f"获取课程失败: HTTP {getattr(e.response, 'status_code', '未知')}")

    def get_assignments(self, class_url):
        """获取作业列表"""
        try:
            class_id = re.search(r'/class/(\d+)/', class_url).group(1)
            detail_url = f"https://www.turnitin.com/class/{class_id}/instructor_home?lang=en_us"
            response = self.session.get(detail_url, headers={'Cookie': self.cookies}, timeout=600)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            assignments = soup.select('tr.assgn-row')
            online_ports = [row.select_one('td.assgn-inbox a[id^="view_inbox_"]')['id'].replace('view_inbox_', '')
                            for row in assignments if row.select_one('td.assgn-inbox a[id^="view_inbox_"]')]
            
            if not online_ports:
                raise ValueError("未找到有效作业端口")
            
            local_ports = list(WebAssignments.objects.filter(status=WebAssignments.Status.AVAILABLE)
                             .values_list('assignment_id', flat=True))
            result = []
            for port in online_ports:
                if port not in local_ports:
                    assign = WebAssignments.objects.create(
                        assignment_id=port,
                        status=WebAssignments.Status.AVAILABLE,
                        upload_count=0
                    )
                else:
                    assign = WebAssignments.objects.get(assignment_id=port)
                result.append({
                    'aid': assign.assignment_id,
                    'title': f"Assignment {assign.assignment_id}",
                    'submission_link': f"{class_url}&port={assign.assignment_id}",
                    'upload_count': assign.upload_count
                })
            return result
        except Exception as e:
            logger.error(f"获取作业失败: {str(e)}")
            raise IOError(f"获取作业失败: {str(e)}")

    def submit(self, assignment_ids, title, filename, userfile, open_id, assign_id_in_db, last_assignment_id):
        """提交作业"""
        classes = self.get_classes()
        if not classes:
            raise ValueError(f"未找到班级 {self.class_name}")
        class_url = classes[0]['url']
        assignments = self.get_assignments(class_url)
        assignments = [a for a in assignments if a['aid'] not in last_assignment_id]
        low_usage_assignment = min(assignments, key=lambda x: x.get('upload_count', 0))
        assignment_id = low_usage_assignment['aid']
        try:
            files = {'userfile': (filename, userfile, 'application/octet-stream')}
            data = {
                'async_request': '1',
                'userID': TurnitinWebConstants.DEFAULT_USER_ID,
                'author_first': TurnitinWebConstants.AUTHOR_FIRST,
                'author_last': TurnitinWebConstants.AUTHOR_LAST,
                'title': title
            }
            submit_url = f"{TurnitinWebConstants.SUBMIT_URL}?aid={assignment_id}&session-id={self.extract_session_id(self.cookies)}&lang={TurnitinWebConstants.LANG_EN_US}"
            response = self.session.post(submit_url, files=files, data=data, headers={
                'Cookie': self.cookies,
                'Referer': f"{TurnitinWebConstants.SUBMIT_URL}?aid={assignment_id}&lang={TurnitinWebConstants.LANG_EN_US}"
            }, timeout=120)
            
            if response.status_code == 302:
                redirect_url = response.headers.get('Location')
                response = self.session.get(redirect_url, headers={'Cookie': self.cookies}, timeout=600)
            
            if response.status_code != 200:
                raise IOError(f"提交失败: HTTP {response.status_code}")
            
            uuid_match = re.search(TurnitinWebConstants.UUID_PATTERN, response.text)
            if not uuid_match:
                raise ValueError("未找到 UUID")
            
            uuid = uuid_match.group(1)
            metadata = self.wait_for_metadata(uuid)
            self.confirm_submission(uuid)
            
            filename_uploaded = self._get_oid_from_assignment(assignment_id)['filename']
            if not filename_uploaded or filename_uploaded[0:10] not in filename:
                logger.error(f'端口文件：{filename_uploaded}, 上传文件:{filename}')
                raise RuntimeError('端口没有上传成功!')
            assign = WebAssignments.objects.get(assignment_id=assignment_id)
            WebAssignments.objects.filter(pk=assign.pk).update(upload_count=F('upload_count') + 1)
        except Exception as e:
            raise RuntimeError("尝试使用端口:%s" % assignment_id)
        return {'metadata': {'assignment_id': assignment_id}}

    def wait_for_metadata(self, uuid):
        """等待提交元数据"""
        session_id = self.extract_session_id(self.cookies)
        metadata_url = f"{TurnitinWebConstants.METADATA_URL}?uuid={uuid}&session-id={session_id}&lang={TurnitinWebConstants.LANG_EN_US}&skip_ready_check=0"
        for _ in range(TurnitinWebConstants.MAX_RETRIES):
            response = self.session.post(metadata_url, data='', headers={
                'Cookie': self.cookies,
                'Accept': TurnitinWebConstants.ACCEPT_JSON
            }, timeout=10)
            if '"status":1' in response.text:
                return {}
            elif '"status":-1' in response.text:
                raise RuntimeError("元数据获取失败")
            time.sleep(TurnitinWebConstants.RETRY_DELAY_MS / 1000)
        raise RuntimeError("元数据获取超时")

    def confirm_submission(self, uuid):
        """确认提交"""
        session_id = self.extract_session_id(self.cookies)
        confirm_url = f"{TurnitinWebConstants.CONFIRM_URL}?lang={TurnitinWebConstants.LANG_EN_US}&sessionid={session_id}&data-state=confirm&uuid={uuid}"
        response = self.session.post(confirm_url, data={'data-state': 'confirm', 'uuid': uuid}, headers={
            'Cookie': self.cookies,
            'Content-Type': TurnitinWebConstants.CONTENT_TYPE_FORM
        }, timeout=600)
        if not response.ok:
            raise IOError(f"确认提交失败: HTTP {response.status_code}")

    def extract_session_id(self, cookies):
        """提取 session-id"""
        for cookie in cookies.split(TurnitinWebConstants.COOKIE_SEPARATOR):
            if cookie.startswith(TurnitinWebConstants.SESSION_ID + '='):
                return cookie[len(TurnitinWebConstants.SESSION_ID + '='):]
        raise ValueError("未找到 session-id")

    def download_ai_file(self, assignment_id, filename):
        """下载 AI 报告"""
        try:
            # Step 1: Get OID
            oid = self._get_oid_from_assignment(assignment_id)['oid']
            print('^'*100, oid)
            
            # Step 2: Extract submission TRN and token
            submission_trn = self._extract_submission_trn(oid)
            print('@'*100, submission_trn)
            
            # Step 3: Get session data
            session_data = self._get_session_data(submission_trn, assignment_id, oid)
            print('&'*100, session_data)
            
            # Step 4: Generate AI report
            job_response = self._generate_ai_report(submission_trn, session_data, filename, assignment_id, oid)
            print('!'*100, job_response)
            
            # Step 5: Get job ID
            job_id = job_response.get('id')
            if not job_id:
                logger.error(f"Failed to get job ID for assignment {assignment_id}")
                return None
            
            # Step 6: Wait for PDF report
            pdf_url = self._wait_for_ai_report(job_id, session_data['session_token'])
            if not pdf_url:
                logger.error(f"PDF report generation timed out or failed for assignment {assignment_id}")
                return None
            
            # Step 7: Download PDF
            pdf_content = self._download_pdf_file(pdf_url, self.get_cookies())
            return pdf_content
        
        except Exception as e:
            logger.error(f"Error downloading AI report for assignment {assignment_id}: {str(e)}", exc_info=True)
            return None

    def _get_oid_from_assignment(self, assignment_id):
        """获取作业的 OID"""
        classes = self.get_classes()
        if not classes:
            raise ValueError(f"未找到班级 {self.class_name}")
        class_url = classes[0]['url']
        self.get_assignments(class_url)
        
        url = f"https://www.turnitin.com/assignment/type/paper/inbox/{assignment_id}?lang={TurnitinWebConstants.LANG_EN_US}"
        response = self.session.get(url, headers={'Cookie': self.cookies}, timeout=600)
        
        if "Log in to Turnitin" in response.text:
            logger.error(f"认证失败 - 被重定向到登录页面 for assignment {assignment_id}")
            raise ValueError("认证失败，请检查 Cookie")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        inbox_table = soup.select_one("table.inbox_table")
        if not inbox_table:
            logger.error(f"未找到 inbox_table for assignment {assignment_id}")
            raise ValueError(f"未找到收件箱表格，可能无提交记录或页面结构变化")
        
        row = inbox_table.select_one(f"tr.student-{TurnitinWebConstants.DEFAULT_USER_ID}")
        if not row:
            logger.error(f"未找到提交行 for assignment {assignment_id} with user ID {TurnitinWebConstants.DEFAULT_USER_ID}")
            raise ValueError(f"未找到提交行，检查用户 ID 或提交记录")
        
        checkbox = row.select_one("input[name=object_checkbox]")
        if not checkbox:
            logger.error(f"未找到 OID checkbox for assignment {assignment_id}")
            raise ValueError(f"未找到 OID 元素，可能页面结构变化")
        
        oid = checkbox.get('value')
        if not oid:
            logger.error(f"OID 为空 for assignment {assignment_id}")
            raise ValueError(f"OID 为空")
        
        logger.info(f"成功获取 OID: {oid} for assignment {assignment_id}")
        return {'oid': oid, 'filename':checkbox.get('title')}

    def _extract_submission_trn(self, oid):
        """提取 submission TRN 和 token"""
        trn_url = f"https://ev.turnitin.com/paper/{oid}/sws_launch_token?lang=en_us&cv=1&output=json"
        response = self.session.get(trn_url, headers={'Cookie': self.cookies}, timeout=600)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Submission TRN response: {data}")
        submissions = data.get('payload', {}).get('config', {}).get('submissions', {})
        for key in submissions.keys():
            if key.startswith('oid:1:'):
                trn = key.split('oid:1:')[1]
                token = data.get('token')
                logger.debug(f"-----------------------------------Extracted TRN: {trn}, Token: {token}")
                return {'trn': trn, 'token': token}
        raise RuntimeError("无法提取 submission-trn")

    def _get_session_data(self, submission_trn, assignment_id, oid):
        """获取 session 数据"""
        session_url = f"https://ev.turnitin.com/assignment/{assignment_id}/session_token?lang=en_us&cv=1&output=json&o={oid}"
        response = self.session.get(session_url, headers={
            'Authorization': f"Bearer {submission_trn['token']}",
            'Cookie': self.cookies
        }, timeout=600)
        response.raise_for_status()
        data = response.json()
        submission_trn['session_token'] = data.get('session_token')
        return submission_trn

    def _generate_ai_report(self, submission_trn, session_data, filename, assignment_id, oid):
        """生成 AI 报告并返回 job ID"""
        sas_api_url = "https://sas-api-usw2.sas.turnitin.com/job"
        submission_trn_value = f"trn:oid:::1:{submission_trn['trn']}"
        logger.debug(f"Submission TRN: {submission_trn_value}")
        logger.debug(f"Session token: {session_data['session_token']}")
        
        request_body = {
            "conversion": "SUBMISSION_REPORT_PDF",
            "providerTag": "sws",
            "submissionTrn": submission_trn_value,
            "extensions": [{
                "name": "aiw",
                "config": {
                    "environment": "prod",
                    "region": "usw2",
                    "locale": "en-US",
                    "sessionToken": session_data['session_token']
                },
                "params": {"version": "2"}
            }],
            "config": {
                "environment": "prod",
                "region": "usw2",
                "locale": "en-US",
                "legacyAuth": session_data['token'],
                "sessionToken": session_data['session_token']
            },
            "params": {
                "author": "No Repository Check",
                "submissionTitle": filename,
                "timeZone": "Asia/Jakarta",
                "orgName": "UIN Raden Intan Lampung",
                "classTitle": self.class_name,
                "assignmentTitle": filename
            }
        }
        headers = {
            'Content-Type': 'application/json',
            'authentication': session_data['session_token']
        }
        logger.debug(f"Request body: {json.dumps(request_body, indent=2)}")
        
        for attempt in range(3):
            response = self.session.post(sas_api_url, json=request_body, headers=headers, timeout=30)
            logger.debug(f"Response: {response.status_code} - {response.text}")
            
            if response.status_code in [200, 201]:
                return {"id": response.text.strip()}
            elif response.status_code == 401:
                logger.warning(f"Attempt {attempt + 1} failed with 401, retrying with new session token...")
                session_data = self._get_session_data(submission_trn, assignment_id, oid)
                request_body["config"]["sessionToken"] = session_data["session_token"]
                request_body["extensions"][0]["config"]["sessionToken"] = session_data["session_token"]
                time.sleep(1)
            else:
                raise RuntimeError(f"Failed to generate AI report: {response.text}")
        
        raise ValueError(f"Failed to generate AI report after 3 attempts: {response.text}")

    def _wait_for_ai_report(self, job_id, session_token):
        """等待 AI 报告生成"""
        sas_api_url = f"https://sas-api-usw2.sas.turnitin.com/job/{job_id}"
        for _ in range(30):
            response = self.session.get(sas_api_url, headers={
                'Content-Type': 'application/json',
                'authentication': session_token
            }, timeout=600)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == "SUCCESS":
                return data.get('url')
            elif data.get('status') == "FAILED":
                raise RuntimeError("AI 报告生成失败")
            time.sleep(1)
        raise ValueError("AI 报告生成超时")

    def _download_pdf_file(self, pdf_url, cookie):
        """下载 PDF 文件"""
        response = self.session.get(pdf_url, headers={
            'Cookie':cookie
        }, timeout=30)
        response.raise_for_status()
        return response.content

    def download_plagiarism_file(self, assignment_id, user_id):
        """下载重复率文件"""
        oid = self._get_oid_from_assignment(assignment_id)['oid']
        download_url = self._get_download_url(assignment_id, oid, f"{assignment_id}_plagiarism.pdf", False, "nonAi", "N", "N")
        return self._download_file(download_url)

    def _get_download_url(self, assignment_id, oid, filename, pdf, pdf_type, filter_reference, filter_quote):
        """获取下载 URL"""
        initial_url = f"{TurnitinWebConstants.DOWNLOAD_URL}{oid}"
        response = self.session.get(initial_url, headers={'Cookie': self.cookies}, timeout=600)
        
        if pdf_type == "nonAi":
            filter_options = {
                "exclude_assignment_template": 1,
                "exclude_quotes": 1, #if filter_quote == "Y" else 0,
                "exclude_biblio": 1, #if filter_reference == "Y" else 0,
                "exclude_small_matches": 0,
                "id": f"{oid}_0",
                "paper": oid,
                "translate_language": 0
            }
            self._send_filter_options(oid, filter_options)
            
            json_body = {"as": 1, "or_type": "similarity", "or_translate_language": 0}
            acquire_url = TurnitinWebConstants.ACQUIRE_DOWNLOAD_URL_LINK % oid
            response = self.session.post(acquire_url, json=json_body, headers={
                'Cookie': self.cookies,
                'Content-Type': 'application/json'
            }, timeout=600)
            data = response.json()
            url = data.get('url')
            
            for _ in range(30):
                check_response = self.session.get(f"{url}&cv=1&output=json", headers={'Cookie': self.cookies}, timeout=600)
                check_data = check_response.json()
                if check_data.get('ready') == 1:
                    return check_data.get('url')
                time.sleep(1)
        raise RuntimeError("文件下载 URL 获取失败")

    def _send_filter_options(self, oid, filter_options):
        """发送过滤选项"""
        url = TurnitinWebConstants.SET_FILTER_URL % oid
        self.session.put(url, json=filter_options, headers={
            'Cookie': self.cookies,
            'Content-Type': 'application/json'
        }, timeout=600)
        
        confirm_url = TurnitinWebConstants.SET_FILTER_URL % oid
        self.session.get(confirm_url, headers={'Cookie': self.cookies}, timeout=600)

    def _download_file(self, download_url):
        """下载文件"""
        response = self.session.get(download_url, headers={'Cookie': self.cookies}, timeout=30)
        return response.content

    def delete_assignment(self, assignment_id, course_url):
        """删除作业"""
        session_id = self.extract_session_id(self.cookies)
        delete_url = f"{course_url}/class_home?lang={TurnitinWebConstants.LANG_EN_US}&session-id={session_id}&victim={assignment_id}"
        response = self.session.post(delete_url, data={'victim': assignment_id}, headers={
            'Cookie': self.cookies,
            'Content-Type': TurnitinWebConstants.CONTENT_TYPE_FORM,
            'Referer': course_url
        }, timeout=600)
        if not response.ok:
            raise IOError(f"删除作业失败: HTTP {response.status_code}")