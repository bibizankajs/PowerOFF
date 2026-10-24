import flet as ft
import os
import asyncio
import winsound
import winreg as reg

def main(page: ft.Page):
    page.title = "PowerOFF"
    page.window_width = 950
    page.window_height = 620
    page.window_resizable = False
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    themes = {
        "dark": {
            "bg_main": "#0d0d0d",
            "bg_panel": "#161616",
            "bg_element": "#242424",
            "fg_primary": "#ffffff",
            "fg_secondary": "#7a7a7a",
            "accent": "#1DB954",
            "danger": "#ff5555"
        },
        "light": {
            "bg_main": "#f4f4f6",
            "bg_panel": "#ffffff",
            "bg_element": "#e5e5ea",
            "fg_primary": "#000000",
            "fg_secondary": "#8e8e93",
            "accent": "#007aff",
            "danger": "#ff3b30"
        }
    }

    current_theme = "dark"
    selected_mode = "shutdown"
    remaining_seconds = 0
    total_seconds = 0
    timer_running = False

    t = themes[current_theme]

    title_text = ft.Text("PowerOFF", size=26, weight=ft.FontWeight.BOLD, color=t["fg_primary"])
    subtitle_text = ft.Text("System Management Hub", size=11, color=t["fg_secondary"])
    
    minutes_input = ft.TextField(
        value="30",
        text_align=ft.TextAlign.CENTER,
        text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, color=t["fg_primary"]),
        bgcolor=t["bg_element"],
        border=ft.InputBorder.NONE,
        border_radius=8,
        height=50
    )

    status_text = ft.Text("Готов к запуску", size=11, color=t["fg_secondary"])

    def check_autostart():
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ)
            reg.QueryValueEx(key, "PowerOFFApp")
            reg.CloseKey(key)
            return True
        except:
            return False

    autostart_switch = ft.Switch(value=check_autostart(), active_color=t["accent"])

    def toggle_autostart(e):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_ALL_ACCESS)
            if autostart_switch.value:
                exe_path = os.path.abspath(__file__)
                reg.SetValueEx(key, "PowerOFFApp", 0, reg.REG_SZ, f'python "{exe_path}"')
            else:
                reg.DeleteValue(key, "PowerOFFApp")
            reg.CloseKey(key)
        except Exception as ex:
            print(f"Ошибка автозапуска: {ex}")

    autostart_switch.on_change = toggle_autostart

    btn_shutdown = ft.Button(content="Выкл", bgcolor=t["accent"], color="#000000", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), expand=True)
    btn_restart = ft.Button(content="Перезагр", bgcolor=t["bg_element"], color=t["fg_primary"], style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), expand=True)
    btn_hibernate = ft.Button(content="Сон", bgcolor=t["bg_element"], color=t["fg_primary"], style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), expand=True)

    def set_mode(mode):
        nonlocal selected_mode
        selected_mode = mode
        pal = themes[current_theme]
        
        btn_shutdown.bgcolor = pal["accent"] if mode == "shutdown" else pal["bg_element"]
        btn_shutdown.color = "#000000" if mode == "shutdown" else pal["fg_primary"]
        
        btn_restart.bgcolor = pal["accent"] if mode == "restart" else pal["bg_element"]
        btn_restart.color = "#000000" if mode == "restart" else pal["fg_primary"]
        
        btn_hibernate.bgcolor = pal["accent"] if mode == "hibernate" else pal["bg_element"]
        btn_hibernate.color = "#000000" if mode == "hibernate" else pal["fg_primary"]
        page.update()

    btn_shutdown.on_click = lambda e: set_mode("shutdown")
    btn_restart.on_click = lambda e: set_mode("restart")
    btn_hibernate.on_click = lambda e: set_mode("hibernate")

    def add_preset(mins):
        try:
            curr = float(minutes_input.value or 0)
            minutes_input.value = str(int(curr + mins))
            page.update()
        except:
            minutes_input.value = str(mins)
            page.update()

    presets_row = ft.Row([
        ft.Button(content="+15м", on_click=lambda e: add_preset(15), expand=True, bgcolor=t["bg_element"], color=t["fg_primary"]),
        ft.Button(content="+30м", on_click=lambda e: add_preset(30), expand=True, bgcolor=t["bg_element"], color=t["fg_primary"]),
        ft.Button(content="+1ч", on_click=lambda e: add_preset(60), expand=True, bgcolor=t["bg_element"], color=t["fg_primary"]),
        ft.Button(content="+2ч", on_click=lambda e: add_preset(120), expand=True, bgcolor=t["bg_element"], color=t["fg_primary"]),
    ], spacing=5)

    progress_ring = ft.ProgressRing(value=1.0, width=130, height=130, stroke_width=10, color=t["accent"], bgcolor=t["bg_element"])
    timer_display_text = ft.Text("00:00", size=22, weight=ft.FontWeight.BOLD, color=t["fg_primary"])

    monitor_stack = ft.Stack([
        ft.Container(content=progress_ring, alignment=ft.Alignment.CENTER),
        ft.Container(content=timer_display_text, alignment=ft.Alignment.CENTER)
    ], width=130, height=130, alignment=ft.Alignment.CENTER)

    async def run_countdown_async():
        nonlocal remaining_seconds, timer_running
        while timer_running and remaining_seconds >= 0:
            mins, secs = divmod(remaining_seconds, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"
            
            timer_display_text.value = time_str
            progress_ring.value = remaining_seconds / total_seconds if total_seconds > 0 else 0
            
            if remaining_seconds <= 3 and remaining_seconds > 0:
                try:
                    winsound.Beep(1000, 200)
                except:
                    pass

            page.update()

            if remaining_seconds == 0:
                break

            await asyncio.sleep(1)
            remaining_seconds -= 1

        if timer_running:
            status_text.value = "Выполнение операции..."
            if selected_mode == "hibernate":
                os.system("shutdown /h")
            timer_running = False
            page.update()

    def start_timer(e):
        nonlocal remaining_seconds, total_seconds, timer_running
        if timer_running:
            return
        try:
            mins = float(minutes_input.value)
            total_seconds = int(mins * 60)
            remaining_seconds = total_seconds
            timer_running = True

            if selected_mode == "shutdown":
                os.system(f"shutdown /s /t {remaining_seconds}")
            elif selected_mode == "restart":
                os.system(f"shutdown /r /t {remaining_seconds}")

            status_text.value = "Таймер активен"
            status_text.color = t["accent"]
            
            page.run_task(run_countdown_async)
            page.update()
        except ValueError:
            status_text.value = "Ошибка ввода"
            status_text.color = t["danger"]
            page.update()

    def cancel_timer(e):
        nonlocal timer_running
        timer_running = False
        os.system("shutdown /a")
        remaining_seconds = 0
        timer_display_text.value = "00:00"
        progress_ring.value = 1.0
        status_text.value = "Таймер сброшен"
        status_text.color = t["fg_secondary"]
        page.update()

    btn_start = ft.Button(content="ЗАПУСТИТЬ ТАЙМЕР", on_click=start_timer, bgcolor=t["accent"], color="#000000" if current_theme=="dark" else "#ffffff", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=45)
    btn_cancel = ft.Button(content="ОТМЕНИТЬ", on_click=cancel_timer, bgcolor=t["bg_element"], color=t["danger"], style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), height=40)

    monitor_inner_box = ft.Container(
        content=monitor_stack,
        bgcolor=t["bg_element"],
        border_radius=16,
        alignment=ft.Alignment.CENTER,
        expand=True
    )

    main_view_content = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("РЕЖИМ РАБОТЫ", size=10, weight=ft.FontWeight.BOLD, color=t["fg_secondary"]),
                ft.Row([btn_shutdown, btn_restart, btn_hibernate], spacing=5),
                ft.Container(height=10),
                ft.Text("ВРЕМЯ (МИНУТЫ)", size=10, weight=ft.FontWeight.BOLD, color=t["fg_secondary"]),
                minutes_input,
                presets_row,
                ft.Container(height=15),
                btn_start
            ]),
            bgcolor=t["bg_panel"], padding=25, border_radius=12, expand=True
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("МОНИТОРИНГ", size=10, weight=ft.FontWeight.BOLD, color=t["fg_secondary"]),
                monitor_inner_box,
                status_text,
                ft.Container(height=15),
                btn_cancel
            ], horizontal_alignment="center"),
            bgcolor=t["bg_panel"], padding=25, border_radius=12, width=380
        )
    ], spacing=15, expand=True)

    def toggle_theme(e):
        nonlocal current_theme
        current_theme = "light" if current_theme == "dark" else "dark"
        apply_theme_colors()

    theme_btn = ft.Button(content="Сменить тему оформления", on_click=toggle_theme, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

    settings_title = ft.Text("Параметры приложения", size=18, weight=ft.FontWeight.BOLD, color=t["fg_primary"])
    autostart_label = ft.Text("Автозапуск вместе с Windows", color=t["fg_primary"])
    theme_label = ft.Text("Тема интерфейса", color=t["fg_primary"])

    settings_view_content = ft.Container(
        content=ft.Column([
            settings_title,
            ft.Divider(color=t["bg_element"]),
            ft.Row([autostart_label, autostart_switch], alignment="spaceBetween"),
            ft.Row([theme_label, theme_btn], alignment="spaceBetween"),
        ], spacing=20),
        bgcolor=t["bg_panel"], padding=30, border_radius=12, expand=True
    )

    content_area = ft.Container(content=main_view_content, padding=20, expand=True)

    def switch_to_settings(e):
        content_area.content = settings_view_content
        settings_btn.content = "✖ Закрыть"
        settings_btn.on_click = switch_to_main
        page.update()

    def switch_to_main(e):
        content_area.content = main_view_content
        settings_btn.content = "⚙ Настройки"
        settings_btn.on_click = switch_to_settings
        page.update()

    settings_btn = ft.Button(content="⚙ Настройки", on_click=switch_to_settings, bgcolor=t["bg_element"], color=t["fg_primary"], style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

    def apply_theme_colors():
        pal = themes[current_theme]
        page.bgcolor = pal["bg_main"]
        title_text.color = pal["fg_primary"]
        subtitle_text.color = pal["fg_secondary"]
        status_text.color = pal["fg_secondary"]
        
        minutes_input.bgcolor = pal["bg_element"]
        minutes_input.text_style.color = pal["fg_primary"]
        
        settings_btn.bgcolor = pal["bg_element"]
        settings_btn.color = pal["fg_primary"]
        
        for container in [main_view_content.controls[0], main_view_content.controls[1], settings_view_content]:
            container.bgcolor = pal["bg_panel"]
            
        progress_ring.color = pal["accent"]
        progress_ring.bgcolor = pal["bg_element"]
        timer_display_text.color = pal["fg_primary"]
        monitor_inner_box.bgcolor = pal["bg_element"]
        
        btn_start.bgcolor = pal["accent"]
        btn_start.color = "#000000" if current_theme == "dark" else "#ffffff"
        
        btn_cancel.bgcolor = pal["bg_element"]
        btn_cancel.color = pal["danger"]
        
        for btn in presets_row.controls:
            btn.bgcolor = pal["bg_element"]
            btn.color = pal["fg_primary"]
            
        settings_title.color = pal["fg_primary"]
        autostart_label.color = pal["fg_primary"]
        theme_label.color = pal["fg_primary"]
        
        set_mode(selected_mode)
        page.update()

    header = ft.Container(
        content=ft.Row([
            ft.Row([title_text, subtitle_text], spacing=15),
            settings_btn
        ], alignment="spaceBetween"),
        padding=20
    )

    page.add(
        ft.Column([
            header,
            content_area
        ], expand=True)
    )
    page.bgcolor = t["bg_main"]

ft.run(main)