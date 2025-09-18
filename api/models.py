from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django_fsm import FSMField, transition

import uuid

class Role(models.Model):
    """角色表"""
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'role'
        verbose_name = '角色'
        verbose_name_plural = '角色'
    
    def __str__(self):
        return self.name

# class User(models.Model):
#     """用户表"""
#     GENDER_CHOICES = [
#         ('male', '男'),
#         ('female', '女'),
#         ('other', '其他'),
#         ('unknown', '未知'),
#     ]
    
#     wechat_id = models.CharField(max_length=255, unique=True)
#     balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
#     gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
#     nick_name = models.CharField(max_length=255, null=True, blank=True)
#     create_datetime = models.DateTimeField()
#     update_datetime = models.DateTimeField()
    
#     class Meta:
#         db_table = 'user'
#         verbose_name = '用户'
#         verbose_name_plural = '用户'
    
#     def __str__(self):
#         return f"{self.nick_name or '未命名用户'} ({self.wechat_id})"

class BackendUser(AbstractBaseUser):
    """后台用户表"""
    username = models.CharField(max_length=64, unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, db_column='role_id')
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'username'
    
    class Meta:
        db_table = 'backend_user'
        verbose_name = '后台用户'
        verbose_name_plural = '后台用户'
    
    def __str__(self):
        return self.username

class AlertMessage(models.Model):
    """
    警报消息模型（无外键约束）
    """
    active_flag = models.BooleanField(default=True, verbose_name="是否激活")
    message = models.CharField(max_length=255, verbose_name="消息内容")


    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 'alert_message'  # 指定数据库表名
        verbose_name = '警报消息'
        verbose_name_plural = '警报消息'

    def __str__(self):
        return f"{self.id}: {self.message[:20]}...({'活跃' if self.active_flag else '禁用'})"



class TurnitinAccount(models.Model):
    """
    账户模型
    - id: 自增主键 (自动创建)
    - username: 账户名
    - password: 密码
    - description: 描述 (可选)
    - is_active: 激活状态
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    username = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="账户名"
    )
    password = models.CharField(
        max_length=128,
        verbose_name="密码"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="描述"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="激活状态"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    class Meta:
        db_table = 'turnitin_account'
        verbose_name = 'Turnitin账户'
        verbose_name_plural = 'Turnitin账户'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({'活跃' if self.is_active else '禁用'})"
    

class WebTurnitinClass(models.Model):
    active_flag = models.CharField(
        max_length=1,
        default='Y',
        choices=[('Y', 'Yes'), ('N', 'No')],
        help_text="标识是否激活，Y=是，N=否"
    )
    class_name = models.CharField(
        max_length=255,
        help_text="class名称"
    )
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        help_text="创建时间"
    )
    update_datetime = models.DateTimeField(
        auto_now=True,
        help_text="更新时间"
    )

    class Meta:
        db_table = 'web_turnitin_class'  # 保持与数据库表名一致
        verbose_name = 'Web class'
        verbose_name_plural = 'Web class'
        constraints = [
            models.CheckConstraint(
                check=models.Q(active_flag__in=['Y', 'N']),
                name='web_turnitin_class_chk_1'
            )
        ]

    def __str__(self):
        return f"{self.class_name} ({'Active' if self.active_flag == 'Y' else 'Inactive'})" 
    

class TurnitinClass(models.Model):
    active_flag = models.CharField(
        max_length=1,
        default='Y',
        choices=[('Y', 'Yes'), ('N', 'No')],
        help_text="标识是否激活，Y=是，N=否"
    )
    class_name = models.CharField(
        max_length=255,
        help_text="class名称"
    )
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        help_text="创建时间"
    )
    update_datetime = models.DateTimeField(
        auto_now=True,
        help_text="更新时间"
    )

    class Meta:
        db_table = 'turnitin_class'  # 保持与数据库表名一致
        verbose_name = 'Turnitin class'
        verbose_name_plural = 'Turnitin class'
        constraints = [
            models.CheckConstraint(
                check=models.Q(active_flag__in=['Y', 'N']),
                name='turnitin_class_chk_1'
            )
        ]

    def __str__(self):
        return f"{self.class_name} ({'Active' if self.active_flag == 'Y' else 'Inactive'})"
    
    

class User(models.Model):
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
    ]

    wechat_id = models.CharField(
        max_length=255,
        verbose_name='微信ID',
        help_text='用户的微信唯一标识'
    )
    
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0.00000000,
        verbose_name='账户余额',
        help_text='用户余额（精确到小数点后8位）'
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name='性别',
        help_text='用户性别'
    )
    
    nick_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='昵称',
        help_text='用户昵称'
    )
    
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='记录创建时间'
    )
    
    update_datetime = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='记录最后更新时间'
    )
    
    available_cnt = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='可用次数',
        help_text='用户可用次数'
    )

    class Meta:
        db_table = 'user'  # 保持与数据库表名一致
        verbose_name = '微信用户'
        verbose_name_plural = '微信用户'
        ordering = ['-available_cnt']
        indexes = [
            models.Index(fields=['wechat_id'], name='wechat_id_idx'),
        ]

    def __str__(self):
        return f"(微信ID: {self.wechat_id})"
    
    
    


class Assignment(models.Model):
    """
    作业表模型
    对应MySQL表结构：assignments
    """
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', '可用'
        DELETED = 'DELETED', '已删除'

    # 字段定义
    assignment_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='作业ID',
        help_text='作业的唯一标识符'
    )
    
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='状态',
        help_text='作业的当前状态'
    )
    
    upload_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='上传次数',
        help_text='作业被上传的次数统计'
    )
    
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='记录的创建时间'
    )
    
    update_datetime = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='记录的最后更新时间'
    )
    
    class_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='班级名称',
        help_text='关联的班级名称'
    )

    class Meta:
        db_table = 'assignments'  # 显式指定数据库表名
        verbose_name = '作业'
        verbose_name_plural = '作业'
        ordering = ['-create_datetime']  # 默认按创建时间降序
        indexes = [
            models.Index(fields=['assignment_id'], name='idx_assignment_id'),
        ]

    def __str__(self):
        return f"{self.assignment_id} ({self.get_status_display()})"

    @property
    def is_available(self):
        """检查作业是否可用"""
        return self.status == self.Status.AVAILABLE

    def increment_upload_count(self):
        """增加上传计数"""
        self.upload_count = models.F('upload_count') + 1
        self.save(update_fields=['upload_count'])
        
        

class UserAssignment(models.Model):
    """
    用户作业关联表（完整字段版本）
    对应MySQL表结构：user_assignments
    """
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', '已提交'
        ANALYSING =  'ANALYSING', '解析中'
        GRADED = 'GRADED', '已评分'
        DOWNLOADED = 'DOWNLOADED', '已下载'
        DELETED = 'DELETED', '删除'
        FAILED = 'FAILED', '失败'

    # 主键（自动创建，无需声明）
    
    # 用户ID字段（对应user.wechat_id）
    user_id = models.CharField(
        max_length=255,
        db_column='user_id',
        verbose_name='用户ID',
        help_text='关联的用户微信ID'
    )
    
    filename = models.CharField(
        max_length=255,
        verbose_name='文件名',
        help_text='上传的原始文件名'
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name='标题',
        help_text='作业显示标题'
    )
    
    assignment_id = models.CharField(
        max_length=50,
        verbose_name='作业ID',
        help_text='关联的作业编号'
    )
    
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name='状态',
        help_text='当前处理状态'
    )
    
    review = models.TextField(
        null=True,
        blank=True,
        verbose_name='评语',
        help_text='教师或系统给出的评语'
    )
    
    filepath = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='文件路径',
        help_text='服务器存储路径'
    )
    
    filter_quote = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='引用过滤',
        help_text='引用检测结果'
    )
    
    filter_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='参考文献过滤',
        help_text='参考文献检测结果'
    )
    
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='记录创建时间'
    )
    
    update_datetime = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='记录最后修改时间'
    )

    class Meta:
        db_table = 'user_assignments'
        verbose_name = '用户作业'
        verbose_name_plural = '用户作业'
        ordering = ['-create_datetime']
        indexes = [
            models.Index(fields=['user_id'], name='idx_user_assignment_user_id'),
            models.Index(fields=['assignment_id'], name='idx_user_assignment_id'),
            models.Index(fields=['status'], name='idx_user_assignment_status'),
        ]

    def __str__(self):
        return f"{self.title} ({self.user_id})"

    # 以下是查询方法（保持之前的功能）
    @classmethod
    def search_by_user(cls, search_term):
        """通过wechat_id或用户id搜索"""
        from .models import User
        if search_term.isdigit():
            try:
                user = User.objects.get(id=int(search_term))
                return cls.objects.filter(user_id=user.wechat_id)
            except User.DoesNotExist:
                return cls.objects.none()
        return cls.objects.filter(user_id=search_term)

    @property
    def user_info(self):
        """动态获取关联用户信息"""
        from .models import User
        try:
            return User.objects.get(wechat_id=self.user_id)
        except User.DoesNotExist:
            return None
        
        
        
from django.db import models
from django.core.validators import MinValueValidator

class PackageConfig(models.Model):
    """
    套餐配置表
    对应MySQL表：package_config
    """
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='价格',
        help_text='套餐价格（精确到小数点后2位）',
        validators=[MinValueValidator(0.01)]  # 价格必须大于0
    )
    
    cnt = models.IntegerField(
        verbose_name='数量',
        help_text='套餐包含的次数',
        validators=[MinValueValidator(1)]  # 数量必须大于0
    )

    class Meta:
        db_table = 'package_config'  # 指定数据库表名
        verbose_name = '套餐配置'
        verbose_name_plural = '套餐配置'
        ordering = ['price']  # 默认按价格排序

    def __str__(self):
        return f"套餐#{self.id} ({self.cnt}次/{self.price}元)"
    
    


class RechargeRecord(models.Model):
    """
    充值记录表
    对应MySQL表：recharge_records
    """
    amount = models.IntegerField(
        verbose_name='充值金额',
        help_text='充值金额（单位：分）'
    )
    
    create_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='记录创建时间'
    )
    
    update_datetime = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='记录最后更新时间'
    )
    
    wechat_id = models.CharField(
        max_length=255,
        verbose_name='微信ID',
        help_text='关联用户的微信ID'
    )
    
    trans_id = models.CharField(
        verbose_name='微信订单号',
        max_length=255,
        help_text='微信订单号'
    )

    class Meta:
        db_table = 'recharge_records'
        verbose_name = '充值记录'
        verbose_name_plural = '充值记录'
        ordering = ['-create_datetime']
        indexes = [
            models.Index(fields=['wechat_id'], name='idx_recharge_wechat_id'),
        ]

    def __str__(self):
        return f"{self.wechat_id} 充值 {self.amount}分"

    @classmethod
    def search_by_user(cls, search_term):
        """
        支持通过User.id或wechat_id搜索充值记录
        参数:
            search_term: 可以是User.id(int)或wechat_id(str)
        返回:
            QuerySet
        """
        from .models import User  # 避免循环导入
        
        # 如果是数字，尝试按User.id查找
        if str(search_term).isdigit():
            try:
                user = User.objects.get(id=int(search_term))
                return cls.objects.filter(wechat_id=user.wechat_id)
            except User.DoesNotExist:
                return cls.objects.none()
        
        # 否则按wechat_id直接搜索
        return cls.objects.filter(wechat_id=search_term)

    @property
    def user_info(self):
        """动态获取关联的User对象"""
        from .models import User
        try:
            return User.objects.get(wechat_id=self.wechat_id)
        except User.DoesNotExist:
            return None
        
        
        

class WebUser(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zh', 'Chinese'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    uid = models.CharField(
            max_length=32, 
            default=lambda: uuid.uuid4().hex,  # 自动生成32字符UUID
            editable=False,  # 禁止编辑
            unique=True,
            verbose_name="UID"
        )    
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, null=True, blank=True)
    nick_name = models.CharField(max_length=255, null=True, blank=True)
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
    available_cnt = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'web_user'
        verbose_name = 'Web User'
        verbose_name_plural = 'Web Users'
        
    def __str__(self):
        return f"{'https://turnitingood.com/'}{self.uid}"


class WebAssignments(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', '可用'
        DELETED = 'DELETED', '已删除'
    
    id = models.BigAutoField(primary_key=True)
    assignment_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(
            max_length=10,
            choices=Status.choices,
            default=Status.AVAILABLE,
            verbose_name='状态',
            help_text='作业的当前状态'
        )   
    upload_count = models.IntegerField(default=0)
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'web_assignments'
        verbose_name = 'Web Assignment'
        verbose_name_plural = 'Web Assignments'
        
    def __str__(self):
        return f"{self.assignment_id} ({self.status})"


class WebUserAssignments(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', '已提交'
        ANALYSING =  'ANALYSING', '解析中'
        GRADED = 'GRADED', '已评分'
        DOWNLOADED = 'DOWNLOADED', '已下载'
        DELETED = 'DELETED', '删除'
        FAILED = 'FAILED', '失败'
    
    status = FSMField(
        choices=Status.choices,
        default=Status.SUBMITTED,
        protected=True  # 禁止直接修改.status属性
    )
    
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255, db_index=True)  # Reference to WebUser without FK constraint
    uid = models.CharField(max_length=33, db_index=True)
    filename = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    origin_title = models.TextField()
    assignment_id = models.CharField(max_length=50)  # Reference to WebAssignments without FK constraint
    # status = status = models.CharField(
    #     max_length=10,
    #     choices=Status.choices,
    #     default=Status.SUBMITTED,
    #     verbose_name='状态',
    #     help_text='作业的当前状态'
    # )
    
    review = models.TextField(null=True, blank=True)
    filepath = models.CharField(max_length=255, null=True, blank=True)
    filter_quote = models.CharField(max_length=255, null=True, blank=True)
    filter_reference = models.CharField(max_length=255, null=True, blank=True)
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
    
    @transition(
    field=status,
    source='*',  # 表示从任何状态
    target=Status.SUBMITTED,
    on_error=Status.SUBMITTED,  # 转换失败时保持原状态
    conditions=[lambda self: False]  # 永远返回False，禁止转换
    )
    def submit(self):
        """
        禁止任何状态转换到SUBMITTED
        """
        pass

    @transition(
        field=status,
        source=Status.FAILED,
        target='*',
        conditions=[lambda self: False]  # 永远返回 False
    )
    def block_failed_transitions(self):
        """禁止从 FAILED 状态转到任何其他状态"""
        raise ValueError("FAILED 状态不可变更")

    @transition(field=status, source=[Status.SUBMITTED, Status.ANALYSING, Status.DOWNLOADED, Status.FAILED], target=Status.DELETED)
    def mark_delete(self):
        """只允许从 SUBMITTED 状态转换到 ANALYSING"""
        pass
    
    @transition(field=status, source=[Status.SUBMITTED], target=Status.ANALYSING)
    def mark_analysising(self):
        """只允许从 SUBMITTED 状态转换到 ANALYSING"""
        pass
    
    @transition(field=status, source=[Status.ANALYSING], target=Status.DOWNLOADED)
    def mark_downloaded(self):
        """只允许从 ANALYSING 状态转换到 DOWNLOADED"""
        pass

    @transition(field=status, source=[Status.SUBMITTED, Status.ANALYSING], target=Status.FAILED)
    def mark_failed(self):
        """任何状态都可以标记为失败（但失败后不可逆）"""
        pass
    
    class Meta:
        db_table = 'web_user_assignments'
        verbose_name = 'Web User Assignment'
        verbose_name_plural = 'Web User Assignments'
        indexes = [
            models.Index(fields=['user_id', 'uid'], name='idx_user_assign_user'),
            models.Index(fields=['assignment_id'], name='idx_user_assign_assign'),
            models.Index(fields=['status'], name='idx_user_assign_status'),
        ]
        
    def __str__(self):
        return f"{self.title} ({self.status}) by User {self.user_id}"