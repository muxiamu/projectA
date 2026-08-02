# ui/main_window.py
import customtkinter as ctk
import threading
from core.api_client import request_response, download_single_image
from core.tag_manager import load_tags_library, save_tags_library, calculate_tag_updates
from core.evaluator import ask_for_evaluate  # 注意：这个将会被 UI 的按钮取代，稍后我们会改造它
from config.config import *
from core.logger import logger

# 设置 CustomTkinter 外观模式（Dark/Light/System）
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎨 个性化图片推荐系统")
        self.geometry("600x500")

        # ---------- 状态变量 ----------
        self.posts = []               # 当前拉取的图片列表
        self.current_index = 0        # 当前处理到第几张
        self.tag_library = load_tags_library(tag_library_dir, tag_library_name)
        self.is_processing = False    # 防连点锁

        # ---------- 界面布局 ----------
        # 1. 顶部标题
        self.title_label = ctk.CTkLabel(self, text="图片推荐引擎", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=10)

        # 2. 信息展示区（显示标签和ID）
        self.info_textbox = ctk.CTkTextbox(self, height=100, state="disabled", wrap="word")
        self.info_textbox.pack(padx=20, pady=10, fill="x")
        self.update_info_box("👋 点击下方【获取图片】开始你的推荐之旅")

        # 3. 进度与状态栏
        self.progress_label = ctk.CTkLabel(self, text="等待开始...", font=("Arial", 12))
        self.progress_label.pack(pady=5)

        # 4. 操作按钮区域
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=15)

        self.fetch_btn = ctk.CTkButton(self.button_frame, text="📥 获取一批图片", command=self.fetch_posts, width=150)
        self.fetch_btn.pack(side="left", padx=10)

        self.like_btn = ctk.CTkButton(self.button_frame, text="❤️ 喜欢 (+1)", command=lambda: self.rate_post(True), state="disabled", fg_color="green", width=120)
        self.like_btn.pack(side="left", padx=10)

        self.dislike_btn = ctk.CTkButton(self.button_frame, text="💔 不喜欢 (-1)", command=lambda: self.rate_post(False), state="disabled", fg_color="red", width=120)
        self.dislike_btn.pack(side="left", padx=10)

        # 5. 退出保存按钮
        self.exit_btn = ctk.CTkButton(self, text="💾 保存并退出", command=self.safe_exit, fg_color="gray")
        self.exit_btn.pack(pady=10)

    # ---------- 核心逻辑与 UI 的桥梁 ----------
    def update_info_box(self, message):
        """更新文本显示区"""
        self.info_textbox.configure(state="normal")
        self.info_textbox.delete("0.0", "end")
        self.info_textbox.insert("0.0", message)
        self.info_textbox.configure(state="disabled")

    def set_status(self, text):
        """更新底部状态栏"""
        self.progress_label.configure(text=text)

    # ---------- 按钮动作 ----------
    def fetch_posts(self):
        """异步拉取图片，防止界面卡死"""
        if self.is_processing:
            return
        self.is_processing = True
        self.fetch_btn.configure(state="disabled")
        self.set_status("🔄 正在向服务器请求图片...")

        # 开启子线程执行耗时任务
        thread = threading.Thread(target=self._fetch_thread, daemon=True)
        thread.start()

    def _fetch_thread(self):
        """子线程执行拉取任务"""
        params = {"limit": 5, "page": 1}  # 你可以从config读取
        self.posts = request_response(params)
        
        # 回到主线程更新 UI（CustomTkinter 线程安全写法）
        self.after(0, self._fetch_complete)

    def _fetch_complete(self):
        """拉取完成后的 UI 回调"""
        self.is_processing = False
        self.fetch_btn.configure(state="normal")
        
        if not self.posts:
            self.set_status("❌ 未获取到图片，请检查网络或日志")
            self.update_info_box("获取失败，请重试")
            return
        
        self.current_index = 0
        self.like_btn.configure(state="normal")
        self.dislike_btn.configure(state="normal")
        self.set_status(f"✅ 成功获取 {len(self.posts)} 张图片")
        self.show_current_post()

    def show_current_post(self):
        """显示当前图片的信息（标签）"""
        if self.current_index < len(self.posts):
            post = self.posts[self.current_index]
            tags = post.get('tags', '无标签')
            img_id = post.get('id', '未知ID')
            
            msg = f"📸 图片 ID: {img_id}\n🏷️ 标签: {tags}\n\n进度: {self.current_index + 1} / {len(self.posts)}"
            self.update_info_box(msg)
            self.set_status(f"请评价第 {self.current_index + 1} 张")
        else:
            self.update_info_box("🎉 所有图片已评价完毕！")
            self.set_status("完成！点【获取一批图片】继续下一轮")
            self.like_btn.configure(state="disabled")
            self.dislike_btn.configure(state="disabled")

    def rate_post(self, is_liked):
        """处理用户评价（主线程，但下载图片较耗时，用线程处理）"""
        if self.is_processing or self.current_index >= len(self.posts):
            return
        
        self.is_processing = True
        self.like_btn.configure(state="disabled")
        self.dislike_btn.configure(state="disabled")
        self.set_status("⏳ 正在下载图片并更新权重...")

        # 用线程执行下载和评价，防止界面卡死
        thread = threading.Thread(target=self._rate_thread, args=(is_liked,), daemon=True)
        thread.start()

    def _rate_thread(self, is_liked):
        """子线程执行评价逻辑"""
        post = self.posts[self.current_index]
        
        # 1. 下载图片（调用 core 函数）
        file_name = download_single_image(post, download_dir)
        
        # 2. 即使下载失败，也允许用户评价（或者跳过，这里我们设计为下载失败则跳过该图）
        if file_name is None:
            logger.warning("下载失败，自动跳过本张")
            self.after(0, self._next_post)
            return

        # 3. 获取标签并更新库（直接调用核心计算逻辑）
        tags_str = post.get('tags', '')
        updates = calculate_tag_updates(tags_str, is_liked)
        for tag, delta in updates.items():
            self.tag_library[tag] = self.tag_library.get(tag, 0) + delta
        
        # 4. 立即保存到硬盘（防止程序崩溃丢数据）
        save_tags_library(tag_library_dir, tag_library_name, self.tag_library)
        
        # 切回主线程，展示下一张
        self.after(0, self._next_post)

    def _next_post(self):
        """切换到下一张图片"""
        self.is_processing = False
        self.current_index += 1
        self.show_current_post()
        if self.current_index < len(self.posts):
            self.like_btn.configure(state="normal")
            self.dislike_btn.configure(state="normal")
        else:
            self.like_btn.configure(state="disabled")
            self.dislike_btn.configure(state="disabled")

    def safe_exit(self):
        """安全退出，保存库"""
        save_tags_library(tag_library_dir, tag_library_name, self.tag_library)
        logger.info("标签库已保存，程序退出")
        self.destroy()

if __name__ == "__main__":
    # 仅用于独立测试 UI
    app = App()
    app.mainloop()