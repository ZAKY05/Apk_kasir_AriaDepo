"""
Users View - Halaman kelola kasir / registrasi akun kasir
Hanya dapat diakses oleh Owner
"""

import tkinter as tk
from tkinter import ttk, messagebox
from styles import COLORS, FONTS, ICONS
import database as db


class UsersView(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS['bg_light'])
        self.user = user
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['bg_light'])
        header.pack(fill='x', padx=25, pady=(25, 15))

        tk.Label(
            header, text=f"{ICONS['user']}  Kelola Kasir",
            font=FONTS['title'], bg=COLORS['bg_light'], fg=COLORS['text_dark']
        ).pack(side='left')

        add_btn = tk.Button(
            header, text=f"{ICONS['add']}  Registrasi Kasir Baru", font=FONTS['button'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_register_dialog, padx=20, pady=8
        )
        add_btn.pack(side='right')
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=COLORS['primary_hover']))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=COLORS['primary']))

        # Info card
        info_frame = tk.Frame(self, bg=COLORS['info_bg'], padx=20, pady=12,
                               highlightbackground=COLORS['border_light'], highlightthickness=1)
        info_frame.pack(fill='x', padx=25, pady=(0, 15))

        tk.Label(
            info_frame,
            text="ℹ️  Daftarkan kasir baru di sini. Setiap kasir akan memiliki akun login sendiri "
                 "dan nama mereka akan tercatat di setiap transaksi.",
            font=FONTS['body'], bg=COLORS['info_bg'], fg=COLORS['info'],
            wraplength=800, justify='left'
        ).pack(anchor='w')

        # Summary
        summary_frame = tk.Frame(self, bg=COLORS['bg_light'])
        summary_frame.pack(fill='x', padx=25, pady=(0, 15))
        summary_frame.columnconfigure((0, 1, 2), weight=1)

        self.total_card = tk.Frame(summary_frame, bg=COLORS['white'], padx=20, pady=15,
                                    highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.total_card.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        tk.Label(self.total_card, text="Total Semua User", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['text_light']).pack(anchor='w')
        self.total_label = tk.Label(self.total_card, text="0", font=FONTS['medium_number'],
                                     bg=COLORS['white'], fg=COLORS['primary'])
        self.total_label.pack(anchor='w')

        self.active_card = tk.Frame(summary_frame, bg=COLORS['white'], padx=20, pady=15,
                                     highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.active_card.grid(row=0, column=1, sticky='nsew', padx=4)
        tk.Label(self.active_card, text="Kasir Aktif", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['text_light']).pack(anchor='w')
        self.active_label = tk.Label(self.active_card, text="0", font=FONTS['medium_number'],
                                      bg=COLORS['white'], fg=COLORS['success'])
        self.active_label.pack(anchor='w')

        self.inactive_card = tk.Frame(summary_frame, bg=COLORS['white'], padx=20, pady=15,
                                       highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.inactive_card.grid(row=0, column=2, sticky='nsew', padx=(8, 0))
        tk.Label(self.inactive_card, text="Kasir Nonaktif", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['text_light']).pack(anchor='w')
        self.inactive_label = tk.Label(self.inactive_card, text="0", font=FONTS['medium_number'],
                                        bg=COLORS['white'], fg=COLORS['danger'])
        self.inactive_label.pack(anchor='w')

        # ===== Action frame - pack di BOTTOM dulu =====
        action_frame = tk.Frame(self, bg=COLORS['bg_light'], pady=5)
        action_frame.pack(side='bottom', fill='x', padx=25, pady=(5, 15))

        edit_btn = tk.Button(
            action_frame, text=f"  {ICONS['edit']}  Edit  ", font=FONTS['body_bold'],
            bg=COLORS['primary_light'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_edit_dialog, pady=8, padx=12
        )
        edit_btn.pack(side='left', padx=(0, 8))
        edit_btn.bind('<Enter>', lambda e: edit_btn.config(bg=COLORS['primary']))
        edit_btn.bind('<Leave>', lambda e: edit_btn.config(bg=COLORS['primary_light']))

        reset_btn = tk.Button(
            action_frame, text=f"  {ICONS['lock']}  Reset Password  ", font=FONTS['body_bold'],
            bg=COLORS['warning'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_reset_password_dialog, pady=8, padx=12
        )
        reset_btn.pack(side='left', padx=(0, 8))
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(bg='#E65100'))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(bg=COLORS['warning']))

        toggle_btn = tk.Button(
            action_frame, text=f"  🔄  Aktifkan/Nonaktifkan  ", font=FONTS['body_bold'],
            bg=COLORS['text_medium'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._toggle_user, pady=8, padx=12
        )
        toggle_btn.pack(side='left')
        toggle_btn.bind('<Enter>', lambda e: toggle_btn.config(bg=COLORS['text_dark']))
        toggle_btn.bind('<Leave>', lambda e: toggle_btn.config(bg=COLORS['text_medium']))

        self.count_label = tk.Label(
            action_frame, text="", font=FONTS['small'],
            bg=COLORS['bg_light'], fg=COLORS['text_light']
        )
        self.count_label.pack(side='right')

        # ===== Tabel user - pack SETELAH action_frame =====
        table_frame = tk.Frame(self, bg=COLORS['white'],
                                highlightbackground=COLORS['border_light'], highlightthickness=1)
        table_frame.pack(fill='both', expand=True, padx=25, pady=(0, 5))

        style = ttk.Style()
        style.configure('Users.Treeview',
                         background=COLORS['white'],
                         foreground=COLORS['text_dark'],
                         fieldbackground=COLORS['white'],
                         font=FONTS['table'],
                         rowheight=42)
        style.configure('Users.Treeview.Heading',
                         background=COLORS['primary'],
                         foreground=COLORS['text_white'],
                         font=FONTS['table_header'],
                         relief='flat')
        style.map('Users.Treeview.Heading',
                   background=[('active', COLORS['primary_hover'])])
        style.map('Users.Treeview',
                   background=[('selected', COLORS['accent_light'])],
                   foreground=[('selected', COLORS['text_dark'])])

        columns = ('id', 'full_name', 'username', 'role', 'status', 'created_at')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                  style='Users.Treeview', selectmode='browse')

        self.tree.heading('id', text='ID')
        self.tree.heading('full_name', text='Nama Lengkap')
        self.tree.heading('username', text='Username')
        self.tree.heading('role', text='Role')
        self.tree.heading('status', text='Status')
        self.tree.heading('created_at', text='Terdaftar')

        self.tree.column('id', width=50, anchor='center')
        self.tree.column('full_name', width=200, anchor='w')
        self.tree.column('username', width=140, anchor='w')
        self.tree.column('role', width=100, anchor='center')
        self.tree.column('status', width=100, anchor='center')
        self.tree.column('created_at', width=160, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.tag_configure('active', background=COLORS['white'])
        self.tree.tag_configure('inactive', background=COLORS['danger_bg'])
        self.tree.tag_configure('owner_row', background=COLORS['info_bg'])

        self.tree.bind('<Double-1>', lambda e: self._show_edit_dialog())



    def refresh_data(self):
        """Refresh data tabel user"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = db.get_all_users()

        total = len(users)
        active_kasir = sum(1 for u in users if u['role'] == 'kasir' and u['is_active'])
        inactive_kasir = sum(1 for u in users if u['role'] == 'kasir' and not u['is_active'])

        for u in users:
            role_display = "👑 Owner" if u['role'] == 'owner' else "🏪 Kasir"
            status_display = "✅ Aktif" if u['is_active'] else "❌ Nonaktif"
            created = u['created_at'][:19] if u['created_at'] else '-'

            if u['role'] == 'owner':
                tags = ('owner_row',)
            elif u['is_active']:
                tags = ('active',)
            else:
                tags = ('inactive',)

            self.tree.insert('', 'end', values=(
                u['id'], u['full_name'], u['username'],
                role_display, status_display, created
            ), tags=tags)

        self.total_label.config(text=str(total))
        self.active_label.config(text=str(active_kasir))
        self.inactive_label.config(text=str(inactive_kasir))
        self.count_label.config(text=f"Total: {total} user")

    def _show_register_dialog(self):
        """Dialog registrasi kasir baru"""
        dialog = tk.Toplevel(self)
        dialog.title("Registrasi Kasir Baru")
        dialog.geometry("480x560")
        dialog.minsize(440, 480)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 240
        y = (dialog.winfo_screenheight() // 2) - 280
        dialog.geometry(f'+{x}+{y}')

        # Header
        tk.Label(dialog, text=f"{ICONS['add']}  Registrasi Kasir Baru",
                 font=FONTS['subtitle'], bg=COLORS['white'],
                 fg=COLORS['primary_dark']).pack(side='top', pady=(15, 10))

        sep = tk.Frame(dialog, bg=COLORS['accent_light'], height=2)
        sep.pack(side='top', fill='x', padx=30)

        # Buttons packed at BOTTOM first so they are ALWAYS visible
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(side='bottom', fill='x', padx=30, pady=15)

        form = tk.Frame(dialog, bg=COLORS['white'], padx=30)
        form.pack(side='top', fill='both', expand=True, pady=10)

        # Nama Lengkap
        tk.Label(form, text="Nama Lengkap", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(3, 2))
        name_var = tk.StringVar()
        name_entry = tk.Entry(form, textvariable=name_var, font=FONTS['input'],
                               relief='solid', bd=1, bg=COLORS['bg_light'])
        name_entry.pack(fill='x', ipady=6)
        name_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                              highlightbackground=COLORS['border'])
        name_entry.focus_set()

        # Username
        tk.Label(form, text="Username", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(8, 2))
        username_var = tk.StringVar()
        username_entry = tk.Entry(form, textvariable=username_var, font=FONTS['input'],
                                   relief='solid', bd=1, bg=COLORS['bg_light'])
        username_entry.pack(fill='x', ipady=6)
        username_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                                  highlightbackground=COLORS['border'])

        # Password
        tk.Label(form, text="Password", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(8, 2))
        password_var = tk.StringVar()
        password_entry = tk.Entry(form, textvariable=password_var, font=FONTS['input'],
                                   show='●', relief='solid', bd=1, bg=COLORS['bg_light'])
        password_entry.pack(fill='x', ipady=6)
        password_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                                  highlightbackground=COLORS['border'])

        # Konfirmasi Password
        tk.Label(form, text="Konfirmasi Password", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(8, 2))
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(form, textvariable=confirm_var, font=FONTS['input'],
                                  show='●', relief='solid', bd=1, bg=COLORS['bg_light'])
        confirm_entry.pack(fill='x', ipady=6)
        confirm_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                                 highlightbackground=COLORS['border'])

        def register():
            full_name = name_var.get().strip()
            username = username_var.get().strip()
            password = password_var.get()
            confirm = confirm_var.get()

            if not full_name:
                messagebox.showwarning("Peringatan", "Nama lengkap harus diisi!", parent=dialog)
                return
            if not username:
                messagebox.showwarning("Peringatan", "Username harus diisi!", parent=dialog)
                return
            if len(username) < 3:
                messagebox.showwarning("Peringatan", "Username minimal 3 karakter!", parent=dialog)
                return
            if not password:
                messagebox.showwarning("Peringatan", "Password harus diisi!", parent=dialog)
                return
            if len(password) < 4:
                messagebox.showwarning("Peringatan", "Password minimal 4 karakter!", parent=dialog)
                return
            if password != confirm:
                messagebox.showwarning("Peringatan", "Password dan konfirmasi tidak cocok!", parent=dialog)
                return

            user_id, msg = db.add_user(username, password, full_name, 'kasir')
            if user_id:
                messagebox.showinfo("Berhasil",
                                     f"Kasir '{full_name}' berhasil didaftarkan!\n\n"
                                     f"Username: {username}\n"
                                     f"Password: {'●' * len(password)}\n\n"
                                     f"Kasir sekarang bisa login ke aplikasi.",
                                     parent=dialog)
                dialog.destroy()
                self.refresh_data()
            else:
                messagebox.showerror("Gagal", msg, parent=dialog)

        save_btn = tk.Button(
            btn_frame, text=f"  💾  Simpan & Daftarkan  ", font=FONTS['button'],
            bg=COLORS['success'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=register, padx=25, pady=8
        )
        save_btn.pack(side='left', padx=(0, 10))
        save_btn.bind('<Enter>', lambda e: save_btn.config(bg='#1B5E20'))
        save_btn.bind('<Leave>', lambda e: save_btn.config(bg=COLORS['success']))

        tk.Button(
            btn_frame, text="Batal", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=30, pady=8
        ).pack(side='left')

    def _show_edit_dialog(self):
        """Dialog edit data kasir"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih user yang ingin diedit!")
            return

        values = self.tree.item(selected[0])['values']
        user_id = values[0]

        dialog = tk.Toplevel(self)
        dialog.title("Edit Data User")
        dialog.geometry("450x380")
        dialog.minsize(420, 320)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 190
        dialog.geometry(f'+{x}+{y}')

        # Header
        tk.Label(dialog, text=f"{ICONS['edit']}  Edit Data User",
                 font=FONTS['subtitle'], bg=COLORS['white'],
                 fg=COLORS['primary_dark']).pack(side='top', pady=(15, 10))

        sep = tk.Frame(dialog, bg=COLORS['accent_light'], height=2)
        sep.pack(side='top', fill='x', padx=30)

        # Buttons packed at BOTTOM first so they are ALWAYS visible
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(side='bottom', fill='x', padx=30, pady=15)

        form = tk.Frame(dialog, bg=COLORS['white'], padx=30)
        form.pack(side='top', fill='both', expand=True, pady=10)

        # Nama Lengkap
        tk.Label(form, text="Nama Lengkap", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(3, 2))
        name_var = tk.StringVar(value=values[1])
        name_entry = tk.Entry(form, textvariable=name_var, font=FONTS['input'],
                               relief='solid', bd=1, bg=COLORS['bg_light'])
        name_entry.pack(fill='x', ipady=6)
        name_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                              highlightbackground=COLORS['border'])
        name_entry.focus_set()

        # Username
        tk.Label(form, text="Username", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(8, 2))
        username_var = tk.StringVar(value=values[2])
        tk.Entry(form, textvariable=username_var, font=FONTS['input'],
                 relief='solid', bd=1, bg=COLORS['bg_light']).pack(fill='x', ipady=6)

        def save():
            full_name = name_var.get().strip()
            username = username_var.get().strip()

            if not full_name or not username:
                messagebox.showwarning("Peringatan", "Semua field harus diisi!", parent=dialog)
                return

            success, msg = db.update_user(user_id, full_name, username)
            if success:
                messagebox.showinfo("Berhasil", "Data user berhasil diupdate!", parent=dialog)
                dialog.destroy()
                self.refresh_data()
            else:
                messagebox.showerror("Gagal", msg, parent=dialog)

        tk.Button(
            btn_frame, text="  💾  Simpan  ", font=FONTS['button'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=save, padx=25, pady=8
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            btn_frame, text="Batal", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=25, pady=8
        ).pack(side='left')

    def _show_reset_password_dialog(self):
        """Dialog reset password"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih user yang ingin direset passwordnya!")
            return

        values = self.tree.item(selected[0])['values']
        user_id = values[0]
        user_name = values[1]

        dialog = tk.Toplevel(self)
        dialog.title(f"Reset Password - {user_name}")
        dialog.geometry("450x380")
        dialog.minsize(420, 320)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 190
        dialog.geometry(f'+{x}+{y}')

        # Header
        tk.Label(dialog, text=f"{ICONS['lock']}  Reset Password",
                 font=FONTS['subtitle'], bg=COLORS['white'],
                 fg=COLORS['primary_dark']).pack(side='top', pady=(15, 5))
        tk.Label(dialog, text=f"User: {user_name}", font=FONTS['body'],
                 bg=COLORS['white'], fg=COLORS['text_light']).pack(side='top', pady=(0, 10))

        sep = tk.Frame(dialog, bg=COLORS['accent_light'], height=2)
        sep.pack(side='top', fill='x', padx=30)

        # Buttons packed at BOTTOM first so they are ALWAYS visible
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(side='bottom', fill='x', padx=30, pady=15)

        form = tk.Frame(dialog, bg=COLORS['white'], padx=30)
        form.pack(side='top', fill='both', expand=True, pady=10)

        tk.Label(form, text="Password Baru", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(3, 2))
        pass_var = tk.StringVar()
        pass_entry = tk.Entry(form, textvariable=pass_var, font=FONTS['input'],
                               show='●', relief='solid', bd=1, bg=COLORS['bg_light'])
        pass_entry.pack(fill='x', ipady=6)
        pass_entry.configure(highlightthickness=1, highlightcolor=COLORS['primary'],
                              highlightbackground=COLORS['border'])
        pass_entry.focus_set()

        tk.Label(form, text="Konfirmasi Password Baru", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(8, 2))
        confirm_var = tk.StringVar()
        tk.Entry(form, textvariable=confirm_var, font=FONTS['input'],
                 show='●', relief='solid', bd=1, bg=COLORS['bg_light']).pack(fill='x', ipady=6)

        def reset():
            password = pass_var.get()
            confirm = confirm_var.get()

            if not password:
                messagebox.showwarning("Peringatan", "Password harus diisi!", parent=dialog)
                return
            if len(password) < 4:
                messagebox.showwarning("Peringatan", "Password minimal 4 karakter!", parent=dialog)
                return
            if password != confirm:
                messagebox.showwarning("Peringatan", "Password tidak cocok!", parent=dialog)
                return

            db.update_user_password(user_id, password)
            messagebox.showinfo("Berhasil", f"Password {user_name} berhasil direset!", parent=dialog)
            dialog.destroy()

        tk.Button(
            btn_frame, text="  💾  Simpan Password  ", font=FONTS['button'],
            bg=COLORS['warning'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=reset, padx=25, pady=8
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            btn_frame, text="Batal", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=25, pady=8
        ).pack(side='left')

    def _toggle_user(self):
        """Aktifkan/nonaktifkan user"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih user!")
            return

        values = self.tree.item(selected[0])['values']
        user_id = values[0]

        # Jangan bisa nonaktifkan diri sendiri
        if user_id == self.user['id']:
            messagebox.showwarning("Peringatan", "Tidak bisa menonaktifkan akun sendiri!")
            return

        user_data = db.get_user_by_id(user_id)
        if user_data['role'] == 'owner':
            messagebox.showwarning("Peringatan", "Tidak bisa menonaktifkan akun owner!")
            return

        action = "nonaktifkan" if user_data['is_active'] else "aktifkan"
        if messagebox.askyesno("Konfirmasi", f"Apakah Anda yakin ingin {action} '{values[1]}'?"):
            db.toggle_user_active(user_id)
            messagebox.showinfo("Berhasil", f"User '{values[1]}' berhasil di{action}!")
            self.refresh_data()
