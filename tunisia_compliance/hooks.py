app_name = "tunisia_compliance"
app_title = "Tunisia Compliance"
app_publisher = "aminos"
app_description = "Custom Localization App for Tunisian Compliance"
app_email = "hamdiahmedamin@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tunisia_compliance",
# 		"logo": "/assets/tunisia_compliance/logo.png",
# 		"title": "Tunisia Compliance",
# 		"route": "/tunisia_compliance",
# 		"has_permission": "tunisia_compliance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tunisia_compliance/css/tunisia_compliance.css"
# app_include_js = "/assets/tunisia_compliance/js/tunisia_compliance.js"

# include js, css files in header of web template
# web_include_css = "/assets/tunisia_compliance/css/tunisia_compliance.css"
# web_include_js = "/assets/tunisia_compliance/js/tunisia_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tunisia_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tunisia_compliance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tunisia_compliance.utils.jinja_methods",
# 	"filters": "tunisia_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tunisia_compliance.install.before_install"
# after_install = "tunisia_compliance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tunisia_compliance.uninstall.before_uninstall"
# after_uninstall = "tunisia_compliance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tunisia_compliance.utils.before_app_install"
# after_app_install = "tunisia_compliance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tunisia_compliance.utils.before_app_uninstall"
# after_app_uninstall = "tunisia_compliance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tunisia_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tunisia_compliance.tasks.all"
# 	],
# 	"daily": [
# 		"tunisia_compliance.tasks.daily"
# 	],
# 	"hourly": [
# 		"tunisia_compliance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tunisia_compliance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tunisia_compliance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tunisia_compliance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tunisia_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tunisia_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tunisia_compliance.utils.before_request"]
# after_request = ["tunisia_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["tunisia_compliance.utils.before_job"]
# after_job = ["tunisia_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tunisia_compliance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
app_include_js = "/assets/tunisia_compliance/js/onboarding.js"
# Runs ONCE for existing companies when app is installed
after_install = "tunisia_compliance.setup.after_install"

# Runs EVERY TIME a new company is created
on_company_creation = "tunisia_compliance.setup.on_create_company"

# Runs BEFORE uninstalling the app
before_uninstall = "tunisia_compliance.uninstall.before_uninstall"

fixtures = [
    # 1. Export ONLY the Address Template for Tunisia
    {
        "doctype": "Address Template",
        "filters": [
            ["country", "=", "Tunisia"]
        ]
    },

    # 2. Export ONLY the Custom Fields needed for your app
    {
        "doctype": "Custom Field",
        "filters": [
            # This is a list of lists. Each inner list is a DocType you've customized.
            # Add more DocTypes here if your app customizes others (e.g., Company, Sales Invoice).
            ["dt", "in", [
                "Company",
                "Employee"
                # Add any other DocTypes you have customized here
            ]]
        ]
    },

    # 3. (Best Practice) Export Property Setters for those same DocTypes
    {
        "doctype": "Property Setter",
        "filters": [
            ["doc_type", "in", [
                "Employee"
                # Make sure this list matches the one in Custom Field
            ]]
        ]
    },

   "Translation",


    # 5. Export Naming Series updates made by your app
    # This is generally safe to export as a whole if you only added prefixes
    # for Doctypes relevant to your app.
    # "Naming Series"
]
