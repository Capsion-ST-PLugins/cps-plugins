import sublime, sublime_plugin
import os, re, sys

sys.path.append(".")
from os import path
from .core import helper
from .core import utils

PLUGIN_NAME = "cps-plugins"
SETTING_KEY = "cps_print_param"
SETTINGS_PRINT_PARAM = {}
DEFAULT_SETTINGS_FILE = "cps.sublime-settings"


if int(sublime.version()) < 3176:
    raise ImportWarning("本插件不支持当前版本，请使用大于等于3176的sublime Text")


def plugin_loaded():
    global SETTINGS_PRINT_PARAM, DEFAULT_SETTINGS_FILE, SETTING_KEY
    SETTINGS_PRINT_PARAM = SettingManager(SETTING_KEY, DEFAULT_SETTINGS_FILE)


class SettingManager:
    def __init__(self, setting_key: str, default_settings: str):
        self.setting_key = setting_key
        self.default_settings = default_settings
        self.default_settings_path = os.path.join(
            sublime.packages_path(), "cps-plugins", ".sublime", default_settings
        )

        self.data = {}

        sublime.set_timeout_async(self.plugin_loaded_async)

    def __getitem__(self, key: str, default={}):
        if key in self.data:
            return self.data.get(key, default)
        else:
            return {}

    def get(self, key: str, default={}):
        return self.__getitem__(key, default)

    def plugin_loaded_async(self):
        """
        @Description 监听用户配置文件
        """
        with open(self.default_settings_path, "r", encoding="utf8") as f:
            self.data = sublime.decode_value(f.read()).get(self.setting_key, {})

        # 读取现有配置
        user_settings = sublime.load_settings(self.default_settings)
        # 添加配置更新事件
        user_settings.add_on_change(self.default_settings, self._on_settings_change)
        # 将最新的配置更新到内部的data，最终以data为准
        utils.recursive_update(self.data, user_settings.to_dict()[self.setting_key])

    def _on_settings_change(self):
        new_settings = sublime.load_settings(self.default_settings).get(
            self.setting_key, {}
        )

        utils.recursive_update(self.data, new_settings)

        return self


class CpsTestCommand(sublime_plugin.TextCommand):
    def run(self, edit, str: str = ""):
        view = self.view
        # 获取当前行
        print(helper.get_currt_selection(view))

        windows = sublime.active_window()

        print(sublime.open_dialog(lambda x: x))


# 快速打印一个参数
class CpsPrintParam(sublime_plugin.TextCommand):
    def run(self, edit):
        global SETTINGS_PRINT_PARAM
        if not SETTINGS_PRINT_PARAM:
            print("配置读取失败")
            return
        settings = SETTINGS_PRINT_PARAM

        view = self.view

        # 获取当前行的region
        currt_region: sublime.Region = self.view.sel()[0]
        currt_line_region = view.full_line(currt_region)

        # 获取下一行
        newt_line_start: int = currt_line_region.b

        # 获取关键字
        select_str = self.view.substr(currt_region)
        if not select_str or len(select_str) <= 0:
            return print("没有任何选择")

        # 获取前置缩进
        currt_line_str = self.view.substr(currt_line_region)

        # 提取前缩进
        res = re.compile(r"^(\s*)?(.*)").findall(currt_line_str)
        if res and len(res) > 0:
            indent = res[0][0]
        else:
            indent = ""

        # 根据不同格式插入不同
        name, ext = os.path.splitext(view.file_name())
        for each in settings.data.values():
            if ext in each["exts"]:
                insert_tmpl = each["template"]
                view.insert(
                    edit,
                    newt_line_start,
                    f"{indent}{insert_tmpl.format(param=select_str)}",
                )
                break


# 打开当前文件的文件夹
class CpsOpenCurrtFolder(sublime_plugin.TextCommand):
    def run(self, edit):
        print("打开当前文件夹")
        # 调用当前激活的窗口来执行 run_command命令(无法使用 self.view 调用 run_command)
        fdir, fname = os.path.split(self.view.file_name())
        sublime.active_window().run_command("open_dir", {"dir": fdir})


# 设置语法
class CpsSetSyntaxCommand(sublime_plugin.TextCommand):
    def run(self, edit, syntax):
        syntaxDict = {
            "html": "Packages/HTML/HTML.sublime-syntax",
            "vue": "Packages/Vue Syntax Highlight/Vue Component.sublime-syntax",
            "js": "Packages/JavaScriptNext - ES6 Syntax/JavaScriptNext.tmLanguage",
        }
        if syntax:
            self.view.set_syntax_file(syntaxDict[syntax])


# 打开配置文件
class CpsEditSettingCommand(sublime_plugin.TextCommand):
    def run(self, edit: sublime.Edit, base_file: str, package_name: str):
        sublime.active_window().run_command(
            "edit_settings",
            {
                "base_file": os.path.join(
                    sublime.packages_path(), __package__, ".sublime", base_file
                ),
                "default": '{\n  "'
                + package_name
                + '":{\n    /*请在插件名称内选项内添加自定义配置*/\n    \n  }\n}',
            },
        )
