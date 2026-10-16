

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Pastikan root folder ada di path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles import COLORS, FONTS, ICONS
import database as db
from views.login import LoginView
from views.dashboard import DashboardView
from views.products import ProductsView
from views.customers import CustomersView
from views.transaction import TransactionView
from views.expenses import ExpensesView
from views.reports import ReportsView
from views.users import UsersView
from views.courier import CourierView
from views.flowmeter import FlowMeterView


class DepoAirApp:
    """Aplikasi utama Kasir Depo Air"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(" Depo Air - Sistem Kasir")
        self.root.geometry("1280x750")
        self.root.minsize(1100, 650)
        self.root.configure(bg=COLORS['bg_light'])

        # Set icon aplikasi dari views/img
        try:
            import os
            from PIL import Image, ImageTk
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views', 'img', 'Aria_Depo.jpeg')
            if os.path.exists(icon_path):
                self._app_icon = ImageTk.PhotoImage(Image.open(icon_path))
                self.root.iconphoto(True, self._app_icon)
        except Exception:
            pass

        # State
        self.current_user = None
        self.current_view = None
        self.active_menu = None
        self.sidebar_buttons = {}

        # Init database
        db.init_database()

        # Show login
        self._show_login()

    def _show_login(self):
        """Tampilkan halaman login"""
        self._clear_main()
        self.root.title(" Depo Air - Login")
        LoginView(self.root, self._on_login_success)

    def _on_login_success(self, user):
        """Callback setelah login berhasil"""
        self.current_user = user
        self._clear_main()
        self._build_main_layout()

        # Default view berdasarkan role
        if user['role'] == 'owner':
            self._switch_view('dashboard')
        else:
            self._switch_view('transaction')

    def _clear_main(self):
        """Hapus semua widget"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def _build_main_layout(self):
        """Bangun layout utama dengan sidebar dan content area"""
        self.root.title(f"💧 Depo Air - {self.current_user['full_name']} ({self.current_user['role'].upper()})")

        # ===== SIDEBAR =====
        self.sidebar = tk.Frame(self.root, bg=COLORS['bg_sidebar'], width=COLORS and 240)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        self.sidebar.configure(width=240)

        # Sidebar header
        sidebar_header = tk.Frame(self.sidebar, bg=COLORS['primary_dark'], padx=20, pady=20)
        sidebar_header.pack(fill='x')

        tk.Label(
            sidebar_header, text=f"{ICONS['water']} DEPO AIR", font=('Segoe UI', 18, 'bold'),
            bg=COLORS['primary_dark'], fg=COLORS['text_white']
        ).pack(anchor='w')

        tk.Label(
            sidebar_header, text="Sistem Kasir", font=FONTS['small'],
            bg=COLORS['primary_dark'], fg=COLORS['accent_light']
        ).pack(anchor='w')

        # User info
        user_frame = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'], padx=20, pady=15)
        user_frame.pack(fill='x')

        tk.Label(
            user_frame, text=f"{ICONS['user']}  {self.current_user['full_name']}",
            font=FONTS['body_bold'], bg=COLORS['bg_sidebar'], fg=COLORS['text_white']
        ).pack(anchor='w')

        role_text = "👑 Owner" if self.current_user['role'] == 'owner' else "🏪 Kasir"
        tk.Label(
            user_frame, text=role_text, font=FONTS['small'],
            bg=COLORS['bg_sidebar'], fg=COLORS['accent_light']
        ).pack(anchor='w', pady=(2, 0))

        sep = tk.Frame(self.sidebar, bg=COLORS['primary'], height=1)
        sep.pack(fill='x', padx=15)

        # Menu items
        menu_frame = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'], pady=10)
        menu_frame.pack(fill='x')

        if self.current_user['role'] == 'owner':
            menus = [
                ('dashboard', ICONS['dashboard'], 'Dashboard'),
                ('products', ICONS['product'], 'Data Produk'),
                ('customers', ICONS['customer'], 'Data Pelanggan'),
                ('users', ICONS['user'], 'Kelola Kasir'),
                ('transaction', ICONS['transaction'], 'Transaksi'),
                ('flowmeter', ICONS.get('flowmeter', '⏱️'), 'Meteran Air'),
                ('expenses', ICONS['expense'], 'Pengeluaran'),
                ('courier', '🚚', 'Pendataan Kurir'),
                ('reports', ICONS['report'], 'Laporan'),
            ]
        else:
            menus = [
                ('transaction', ICONS['transaction'], 'Transaksi'),
                ('flowmeter', ICONS.get('flowmeter', '⏱️'), 'Catat Meteran'),
            ]

        for key, icon, text in menus:
            self._create_sidebar_button(menu_frame, key, icon, text)

        # Spacer
        spacer = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'])
        spacer.pack(fill='both', expand=True)

        # Logout button
        logout_frame = tk.Frame(self.sidebar, bg=COLORS['bg_sidebar'], pady=15)
        logout_frame.pack(fill='x', side='bottom')

        sep2 = tk.Frame(logout_frame, bg=COLORS['primary'], height=1)
        sep2.pack(fill='x', padx=15, pady=(0, 10))

        logout_btn = tk.Button(
            logout_frame, text=f"{ICONS['logout']}   Logout", font=FONTS['sidebar'],
            bg=COLORS['bg_sidebar'], fg=COLORS['text_sidebar'],
            activebackground=COLORS['danger'], activeforeground=COLORS['text_white'],
            relief='flat', cursor='hand2', anchor='w', padx=25, pady=10,
            command=self._logout
        )
        logout_btn.pack(fill='x')
        logout_btn.bind('<Enter>', lambda e: logout_btn.config(bg=COLORS['danger'], fg=COLORS['text_white']))
        logout_btn.bind('<Leave>', lambda e: logout_btn.config(bg=COLORS['bg_sidebar'], fg=COLORS['text_sidebar']))

        # ===== CONTENT AREA =====
        self.content = tk.Frame(self.root, bg=COLORS['bg_light'])
        self.content.pack(side='left', fill='both', expand=True)

    def _create_sidebar_button(self, parent, key, icon, text):
        """Buat tombol sidebar"""
        btn = tk.Button(
            parent, text=f"{icon}   {text}", font=FONTS['sidebar'],
            bg=COLORS['bg_sidebar'], fg=COLORS['text_sidebar'],
            activebackground=COLORS['bg_sidebar_active'],
            activeforeground=COLORS['text_white'],
            relief='flat', cursor='hand2', anchor='w', padx=25, pady=11,
            command=lambda k=key: self._switch_view(k)
        )
        btn.pack(fill='x')
        btn.bind('<Enter>', lambda e, b=btn, k=key: self._menu_hover(b, k, True))
        btn.bind('<Leave>', lambda e, b=btn, k=key: self._menu_hover(b, k, False))

        self.sidebar_buttons[key] = btn

    def _menu_hover(self, btn, key, entering):
        """Efek hover pada menu sidebar"""
        if key == self.active_menu:
            return  # Jangan ubah style menu aktif
        if entering:
            btn.config(bg=COLORS['bg_sidebar_hover'], fg=COLORS['text_white'])
        else:
            btn.config(bg=COLORS['bg_sidebar'], fg=COLORS['text_sidebar'])

    def _switch_view(self, view_name):
        """Pindah tampilan"""
        # Update menu aktif
        if self.active_menu and self.active_menu in self.sidebar_buttons:
            self.sidebar_buttons[self.active_menu].config(
                bg=COLORS['bg_sidebar'], fg=COLORS['text_sidebar'],
                font=FONTS['sidebar']
            )

        self.active_menu = view_name
        if view_name in self.sidebar_buttons:
            self.sidebar_buttons[view_name].config(
                bg=COLORS['bg_sidebar_active'], fg=COLORS['text_white'],
                font=FONTS['sidebar_bold']
            )

        # Clear content
        for widget in self.content.winfo_children():
            widget.destroy()

        # Load view
        view_map = {
            'dashboard': DashboardView,
            'products': ProductsView,
            'customers': CustomersView,
            'users': UsersView,
            'transaction': TransactionView,
            'flowmeter': FlowMeterView,
            'expenses': ExpensesView,
            'courier': CourierView,
            'reports': ReportsView,
        }

        view_class = view_map.get(view_name)
        if view_class:
            self.current_view = view_class(self.content, self.current_user)
            self.current_view.pack(fill='both', expand=True)

    def _logout(self):
        """Logout dan kembali ke login"""
        if messagebox.askyesno("Logout", "Apakah Anda yakin ingin logout?"):
            self.current_user = None
            self.active_menu = None
            self.sidebar_buttons = {}
            self._show_login()

    def run(self):
        """Jalankan aplikasi"""
        # Center window di layar
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

        self.root.mainloop()


if __name__ == "__main__":
    app = DepoAirApp()
    app.run()
