def ask_for_evaluate():
    """
    询问用户对当前图片的评价      
    返回: True (喜欢), False (不喜欢), 或 None (无效输入)
    """
    while True:
        choice = input('Like or dislike?(y/n):').strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print('请输入y或n')