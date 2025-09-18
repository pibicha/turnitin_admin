from django.contrib import admin
from .models import AlertMessage, TurnitinAccount, TurnitinClass,\
    User, Assignment, UserAssignment,PackageConfig,RechargeRecord,\
        WebUser, WebAssignments, WebUserAssignments, WebTurnitinClass

admin.site.register(AlertMessage)
admin.site.register(TurnitinAccount)
admin.site.register(TurnitinClass)
admin.site.register(WebTurnitinClass)

admin.site.register(PackageConfig)


# admin.site.register(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'wechat_id', 'nick_name', 'gender', 'balance', 'available_cnt', 'create_datetime', 'update_datetime')  # 显示的字段
    search_fields = ('id', 'wechat_id')  # 启用 id 和 wechat_id 搜索
    list_filter = ('create_datetime',)  # 可选：添加性别和创建时间的筛选
    ordering = ('-available_cnt',)  # 按 available_cnt 降序排列
    
from django.contrib import admin

@admin.register(UserAssignment)
class UserAssignmentAdmin(admin.ModelAdmin):
    # 1. 列表页显示的字段（包含关联用户信息）
    list_display = (
        'id',
        'user_id',
        'display_user_nickname',  # 自定义关联用户昵称
        'filename',
        'title',
        'assignment_id',
        'status',
        'create_datetime',
        'update_datetime'
    )
    
    # 2. 搜索配置（支持通过user_id/assignment_id搜索）
    search_fields = (
        'user_id',          # 直接搜索微信ID
        'assignment_id',    # 搜索作业ID
        'title',            # 按标题搜索
    )
    
    # 3. 筛选面板
    list_filter = (
        'status',           # 状态筛选
        'create_datetime',  # 创建时间范围筛选
    )
    
    # 4. 默认排序（按创建时间倒序）
    ordering = ('-create_datetime',)
    
    # 5. 可快速编辑的字段
    list_editable = ('status',)
    
    # 6. 自定义字段显示方法
    def display_user_nickname(self, obj):
        """显示关联用户的昵称"""
        user = obj.user_info  # 使用之前定义的user_info属性
        return user.nick_name if user else '--'
    display_user_nickname.short_description = '用户昵称'
    display_user_nickname.admin_order_field = 'user_id'  # 支持按user_id排序

    # 7. 重写get_search_results实现智能搜索
    def get_search_results(self, request, queryset, search_term):
        """
        重写搜索逻辑，支持：
        1. 直接输入微信ID（精确匹配）
        2. 输入用户ID（自动关联查询）
        """
        # 调用Model的安全搜索方法
        result_queryset = UserAssignment.search_by_user(search_term)
        
        # 如果按用户ID搜索无结果，尝试普通搜索
        if not result_queryset.exists():
            return super().get_search_results(request, queryset, search_term)
            
        return result_queryset, False
    

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    # 1. 显示所有字段（按Model定义顺序）
    list_display = (
        'id',
        'assignment_id',
        'status',
        'upload_count',
        'class_name',
        'create_datetime',
        'update_datetime'
    )
    
    # 2. 按assignment_id搜索（精确匹配）
    search_fields = ('assignment_id',)
    
    # 3. 添加常用筛选条件
    list_filter = (
        'status',  # 状态筛选
        'create_datetime',  # 创建时间范围筛选
    )
    
    # 4. 默认排序（按创建时间降序）
    ordering = ('-create_datetime',)
    
    # 6. 快速编辑功能（列表页可直接修改状态）
    # list_editable = ('status', 'class_name')
    
    # 7. 自定义字段显示（可选）
    def formatted_assignment_id(self, obj):
        """格式化作业ID显示"""
        return f"作业-{obj.assignment_id}"
    formatted_assignment_id.short_description = '作业ID'
    
    # 8. 只读字段
    readonly_fields = ('create_datetime', 'update_datetime')
    
    
@admin.register(RechargeRecord)
class RechargeRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'wechat_id', 'trans_id', 'display_user', 'amount', 'create_datetime')
    search_fields = ('wechat_id',)
    list_filter = ('create_datetime',)
    
    def display_user(self, obj):
        user = obj.user_info
        return f"短ID: 【{user.id}】" if user else ""
    display_user.short_description = '关联用户'
    
    def get_search_results(self, request, queryset, search_term):
        if search_term.isdigit():
            from .models import User
            try:
                user = User.objects.get(id=int(search_term))
                return queryset.filter(wechat_id=user.wechat_id), False
            except User.DoesNotExist:
                pass
        return super().get_search_results(request, queryset, search_term)
    
class WebAdminSite(admin.AdminSite):
    site_header = 'Web平台管理'
    site_title = 'Web管理后台'
    index_title = '数据管理'




@admin.register(WebAssignments)
class WebAssignmentsAdmin(admin.ModelAdmin):
    list_display = ('assignment_id', 'status', 'upload_count', 'create_datetime')
    search_fields = ('assignment_id',)
    list_filter = ('status', 'create_datetime')
    list_editable = ('status',)
    readonly_fields = ('create_datetime', 'update_datetime')

@admin.register(WebUserAssignments)
class WebUserAssignmentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'show_user', 'assignment_id', 'title', 'status', 'create_datetime')
    search_fields = ('user_id', 'assignment_id', 'title', 'assignment_id')
    list_filter = ('status', 'create_datetime')
    list_editable = ('status',)
    
    # 显示关联用户信息
    def show_user(self, obj):
        return f"{obj.user_id} ({obj.uid})"
    show_user.short_description = '用户信息'
    
    

@admin.register(WebUser)
class WebUserAdmin(admin.ModelAdmin):
    # 设置只读字段（包含自动生成的字段）
    readonly_fields = ('uid', 'create_datetime', 'update_datetime')
    search_fields = ('uid',)
    # 表单字段排列顺序
    fieldsets = [
        (None, {
            'fields': [
                'uid',
                'language',
                'nick_name',
                'available_cnt',
                'create_datetime',
                'update_datetime'
            ]
        }),
    ]
    
    # 添加页面隐藏的字段（可选）
    def get_exclude(self, request, obj=None):
        if obj is None:  # 判断是否是添加页面
            return []  # 添加页面显示所有字段
        return super().get_exclude(request, obj)

    # 批量插入方法1：批量插入 100 个中文用户，1 次使用机会
    def batch_insert_chinese_1(self, request, queryset):
        new_users = [
            WebUser(language='zh', nick_name=f'用户{i}', available_cnt=1)
            for i in range(100)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 100 个中文用户，1 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法2：批量插入 10 个中文用户，3 次使用机会
    def batch_insert_chinese_3(self, request, queryset):
        new_users = [
            WebUser(language='zh', nick_name=f'用户{i}', available_cnt=3)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个中文用户，3 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法3：批量插入 10 个中文用户，5 次使用机会
    def batch_insert_chinese_5(self, request, queryset):
        new_users = [
            WebUser(language='zh', nick_name=f'用户{i}', available_cnt=5)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个中文用户，5 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法4：批量插入 10 个中文用户，12 次使用机会
    def batch_insert_chinese_12(self, request, queryset):
        new_users = [
            WebUser(language='zh', nick_name=f'用户{i}', available_cnt=12)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个中文用户，12 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法5：批量插入 100 个英文用户，1 次使用机会
    def batch_insert_english_1(self, request, queryset):
        new_users = [
            WebUser(language='en', nick_name=f'User{i}', available_cnt=1)
            for i in range(100)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 100 个英文用户，1 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法6：批量插入 10 个英文用户，3 次使用机会
    def batch_insert_english_3(self, request, queryset):
        new_users = [
            WebUser(language='en', nick_name=f'User{i}', available_cnt=3)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个英文用户，3 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法7：批量插入 10 个英文用户，5 次使用机会
    def batch_insert_english_5(self, request, queryset):
        new_users = [
            WebUser(language='en', nick_name=f'User{i}', available_cnt=5)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个英文用户，5 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 批量插入方法8：批量插入 10 个英文用户，12 次使用机会
    def batch_insert_english_12(self, request, queryset):
        new_users = [
            WebUser(language='en', nick_name=f'User{i}', available_cnt=12)
            for i in range(10)
        ]
        WebUser.objects.bulk_create(new_users)
        
        uids = ['https://turnitingood.com/' + user.uid for user in new_users]
        self.message_user(request, f"成功批量插入 10 个英文用户，12 次使用机会。插入的用户 UID：{', '.join(map(str, uids))}")

    # 为操作添加描述
    batch_insert_chinese_1.short_description = "批量插入 100 个中文用户，1 次使用机会"
    batch_insert_chinese_3.short_description = "批量插入 10 个中文用户，3 次使用机会"
    batch_insert_chinese_5.short_description = "批量插入 10 个中文用户，5 次使用机会"
    batch_insert_chinese_12.short_description = "批量插入 10 个中文用户，12 次使用机会"
    batch_insert_english_1.short_description = "批量插入 100 个英文用户，1 次使用机会"
    batch_insert_english_3.short_description = "批量插入 10 个英文用户，3 次使用机会"
    batch_insert_english_5.short_description = "批量插入 10 个英文用户，5 次使用机会"
    batch_insert_english_12.short_description = "批量插入 10 个英文用户，12 次使用机会"

    # 将批量插入操作添加到 actions 中
    actions = [
        'batch_insert_chinese_1',
        'batch_insert_chinese_3',
        'batch_insert_chinese_5',
        'batch_insert_chinese_12',
        'batch_insert_english_1',
        'batch_insert_english_3',
        'batch_insert_english_5',
        'batch_insert_english_12',
    ]
