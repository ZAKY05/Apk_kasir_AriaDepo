"""
Courier View - Halaman pendataan kurir dan biaya antar
Digunakan oleh Owner untuk melacak uang antar kurir
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from styles import COLORS, FONTS, ICONS, format_currency, format_number
import database as db


class CourierView(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS['bg_light'])
        self.user = user
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=COLORS['bg_light'])
        header.pack(fill='x', padx=20, pady=(20, 10))

        tk.Label(
            header, text="🚚  Pendataan Kurir & Ongkir",
            font=FONTS['title'], bg=COLORS['bg_light'], fg=COLORS['text_dark']
        ).pack(side='left')

        refresh_btn = tk.Button(
            header, text=f"  {ICONS['refresh']}  Refresh  ", font=FONTS['button'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self.refresh_data, padx=12, pady=6
        )
        refresh_btn.pack(side='right')
        refresh_btn.bind('<Enter>', lambda e: refresh_btn.config(bg=COLORS['primary_hover']))
        refresh_btn.bind('<Leave>', lambda e: refresh_btn.config(bg=COLORS['primary']))

        # Main content with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 15))

        # Tab 1: Ringkasan Kurir
        self.summary_tab = tk.Frame(self.notebook, bg=COLORS['white'])
        self.notebook.add(self.summary_tab, text="  📊 Ringkasan Kurir  ")

        # Tab 2: Detail Antaran
        self.detail_tab = tk.Frame(self.notebook, bg=COLORS['white'])
        self.notebook.add(self.detail_tab, text="  📋 Detail Antaran  ")

        # Tab 3: Riwayat Serah Terima
        self.history_tab = tk.Frame(self.notebook, bg=COLORS['white'])
        self.notebook.add(self.history_tab, text="  📜 Riwayat Serah Terima  ")

        self._build_summary_tab()
        self._build_detail_tab()
        self._build_history_tab()

    def _build_summary_tab(self):
        """Tab ringkasan per kurir"""
        # Stats cards
        self.stats_frame = tk.Frame(self.summary_tab, bg=COLORS['white'], padx=15, pady=15)
        self.stats_frame.pack(fill='x')

        # Table
        table_frame = tk.Frame(self.summary_tab, bg=COLORS['white'], padx=15, pady=(0, 15))
        table_frame.pack(fill='both', expand=True)

        tk.Label(table_frame, text="Ringkasan Per Kurir", font=FONTS['heading'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 10))

        # Treeview
        columns = ('courier', 'total_antar', 'pending', 'collected', 'settled')
        self.summary_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)

        self.summary_tree.heading('courier', text='Nama Kurir')
        self.summary_tree.heading('total_antar', text='Total Antaran')
        self.summary_tree.heading('pending', text='Pending (Belum Diambil)')
        self.summary_tree.heading('collected', text='Dikumpulkan (Belum Setor)')
        self.summary_tree.heading('settled', text='Sudah Diserahkan')

        self.summary_tree.column('courier', width=150)
        self.summary_tree.column('total_antar', width=100, anchor='center')
        self.summary_tree.column('pending', width=180, anchor='center')
        self.summary_tree.column('collected', width=200, anchor='center')
        self.summary_tree.column('settled', width=180, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)
        self.summary_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Action buttons
        action_frame = tk.Frame(self.summary_tab, bg=COLORS['white'], padx=15, pady=10)
        action_frame.pack(fill='x', side='bottom')

        collect_btn = tk.Button(
            action_frame, text="  💵  Kurir Ambil Uang (Mark Collected)  ", font=FONTS['button'],
            bg=COLORS['warning'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._mark_collected, padx=12, pady=8
        )
        collect_btn.pack(side='left', padx=(0, 10))
        collect_btn.bind('<Enter>', lambda e: collect_btn.config(bg='#E65100'))
        collect_btn.bind('<Leave>', lambda e: collect_btn.config(bg=COLORS['warning']))

        settle_btn = tk.Button(
            action_frame, text="  ✅  Serah Terima (Setor Semua)  ", font=FONTS['button'],
            bg=COLORS['success'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._settle_courier, padx=12, pady=8
        )
        settle_btn.pack(side='left')
        settle_btn.bind('<Enter>', lambda e: settle_btn.config(bg='#1B5E20'))
        settle_btn.bind('<Leave>', lambda e: settle_btn.config(bg=COLORS['success']))

    def _build_detail_tab(self):
        """Tab detail antaran"""
        # Filters
        filter_frame = tk.Frame(self.detail_tab, bg=COLORS['bg_light'], padx=15, pady=10)
        filter_frame.pack(fill='x')

        tk.Label(filter_frame, text="Filter Kurir:", font=FONTS['body_bold'],
                 bg=COLORS['bg_light'], fg=COLORS['text_dark']).pack(side='left')

        self.filter_courier_var = tk.StringVar(value="Semua Kurir")
        self.filter_courier_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_courier_var,
            font=FONTS['small'], state='readonly', width=20
        )
        self.filter_courier_combo.pack(side='left', padx=8)
        self.filter_courier_combo.bind('<<ComboboxSelected>>', lambda e: self._load_detail_data())

        tk.Label(filter_frame, text="Status:", font=FONTS['body_bold'],
                 bg=COLORS['bg_light'], fg=COLORS['text_dark']).pack(side='left', padx=(15, 0))

        self.filter_status_var = tk.StringVar(value="Semua")
        status_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_status_var,
            values=["Semua", "Pending", "Collected", "Settled"],
            font=FONTS['small'], state='readonly', width=12
        )
        status_combo.pack(side='left', padx=8)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self._load_detail_data())

        # Table
        table_frame = tk.Frame(self.detail_tab, bg=COLORS['white'], padx=15, pady=(0, 10))
        table_frame.pack(fill='both', expand=True)

        detail_cols = ('id', 'date', 'invoice', 'customer', 'courier', 'fee', 'status')
        self.detail_tree = ttk.Treeview(table_frame, columns=detail_cols, show='headings', height=12)

        self.detail_tree.heading('id', text='ID')
        self.detail_tree.heading('date', text='Tanggal')
        self.detail_tree.heading('invoice', text='No. Invoice')
        self.detail_tree.heading('customer', text='Pelanggan')
        self.detail_tree.heading('courier', text='Kurir')
        self.detail_tree.heading('fee', text='Ongkir')
        self.detail_tree.heading('status', text='Status')

        self.detail_tree.column('id', width=50, anchor='center')
        self.detail_tree.column('date', width=130, anchor='center')
        self.detail_tree.column('invoice', width=140)
        self.detail_tree.column('customer', width=150)
        self.detail_tree.column('courier', width=120)
        self.detail_tree.column('fee', width=100, anchor='right')
        self.detail_tree.column('status', width=100, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=scrollbar.set)
        self.detail_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Action buttons for detail
        action_frame = tk.Frame(self.detail_tab, bg=COLORS['white'], padx=15, pady=10)
        action_frame.pack(fill='x', side='bottom')

        mark_one_btn = tk.Button(
            action_frame, text="  💵  Tandai Terpilih Sudah Diambil  ", font=FONTS['button'],
            bg=COLORS['info'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._mark_selected_collected, padx=12, pady=8
        )
        mark_one_btn.pack(side='left')
        mark_one_btn.bind('<Enter>', lambda e: mark_one_btn.config(bg=COLORS['primary_hover']))
        mark_one_btn.bind('<Leave>', lambda e: mark_one_btn.config(bg=COLORS['info']))

    def _build_history_tab(self):
        """Tab riwayat serah terima"""
        table_frame = tk.Frame(self.history_tab, bg=COLORS['white'], padx=15, pady=15)
        table_frame.pack(fill='both', expand=True)

        tk.Label(table_frame, text="Riwayat Serah Terima Uang Kurir", font=FONTS['heading'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 10))

        history_cols = ('id', 'date', 'courier', 'deliveries', 'amount', 'user', 'notes')
        self.history_tree = ttk.Treeview(table_frame, columns=history_cols, show='headings', height=12)

        self.history_tree.heading('id', text='ID')
        self.history_tree.heading('date', text='Tanggal')
        self.history_tree.heading('courier', text='Kurir')
        self.history_tree.heading('deliveries', text='Jml Antaran')
        self.history_tree.heading('amount', text='Total Uang')
        self.history_tree.heading('user', text='Diterima Oleh')
        self.history_tree.heading('notes', text='Catatan')

        self.history_tree.column('id', width=50, anchor='center')
        self.history_tree.column('date', width=120, anchor='center')
        self.history_tree.column('courier', width=120)
        self.history_tree.column('deliveries', width=100, anchor='center')
        self.history_tree.column('amount', width=130, anchor='right')
        self.history_tree.column('user', width=130)
        self.history_tree.column('notes', width=180)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def refresh_data(self):
        """Refresh semua data"""
        self._load_stats()
        self._load_summary_data()
        self._load_detail_data()
        self._load_history_data()
        self._load_courier_filter()

    def _load_stats(self):
        """Load statistik delivery"""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        try:
            stats = db.get_delivery_stats()
        except Exception:
            stats = {'pending_total': 0, 'pending_count': 0,
                     'collected_total': 0, 'collected_count': 0,
                     'today_total': 0, 'today_count': 0}

        cards_data = [
            ("Antaran Hari Ini", f"{stats['today_count']} kali", format_currency(stats['today_total']),
             COLORS['primary'], COLORS['accent_light']),
            ("Pending (Belum Diambil)", f"{stats['pending_count']} antaran", format_currency(stats['pending_total']),
             COLORS['warning'], COLORS['warning_bg']),
            ("Dikumpulkan (Belum Setor)", f"{stats['collected_count']} antaran", format_currency(stats['collected_total']),
             COLORS['info'], COLORS['info_bg']),
        ]

        for i, (title, count_text, amount_text, color, bg) in enumerate(cards_data):
            card = tk.Frame(self.stats_frame, bg=bg, padx=20, pady=15,
                            highlightbackground=color, highlightthickness=2)
            card.pack(side='left', fill='x', expand=True, padx=(0, 10) if i < 2 else (0, 0))

            tk.Label(card, text=title, font=FONTS['body_bold'], bg=bg, fg=COLORS['text_dark']).pack(anchor='w')
            tk.Label(card, text=amount_text, font=FONTS['medium_number'], bg=bg, fg=color).pack(anchor='w', pady=(3, 0))
            tk.Label(card, text=count_text, font=FONTS['small'], bg=bg, fg=COLORS['text_medium']).pack(anchor='w')

    def _load_summary_data(self):
        """Load ringkasan per kurir"""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        try:
            summary = db.get_courier_summary()
        except Exception:
            summary = []

        for s in summary:
            self.summary_tree.insert('', 'end', values=(
                s['courier_name'],
                f"{s['total_deliveries']} kali",
                f"{s['pending_count']}x = {format_currency(s['pending_amount'])}",
                f"{s['collected_count']}x = {format_currency(s['collected_amount'])}",
                f"{s['settled_count']}x = {format_currency(s['settled_amount'])}",
            ))

    def _load_detail_data(self):
        """Load detail antaran"""
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        courier_filter = self.filter_courier_var.get()
        status_filter = self.filter_status_var.get()

        courier_name = None if courier_filter == "Semua Kurir" else courier_filter
        status = None
        if status_filter == "Pending":
            status = "pending"
        elif status_filter == "Collected":
            status = "collected"
        elif status_filter == "Settled":
            status = "settled"

        try:
            fees = db.get_delivery_fees(courier_name=courier_name, status=status)
        except Exception:
            fees = []

        status_display = {'pending': '⏳ Pending', 'collected': '💵 Diambil', 'settled': '✅ Disetor'}

        for f in fees:
            date_str = f.get('transaction_date', f.get('created_at', ''))
            try:
                dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except (ValueError, TypeError):
                pass

            self.detail_tree.insert('', 'end', iid=str(f['id']), values=(
                f['id'],
                date_str,
                f.get('invoice_number', '-'),
                f.get('customer_name', '-'),
                f['courier_name'],
                format_currency(f['delivery_fee']),
                status_display.get(f['status'], f['status']),
            ))

    def _load_history_data(self):
        """Load riwayat serah terima"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        try:
            settlements = db.get_courier_settlements()
        except Exception:
            settlements = []

        for s in settlements:
            date_str = s.get('settlement_date', '')
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                date_str = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass

            self.history_tree.insert('', 'end', values=(
                s['id'],
                date_str,
                s['courier_name'],
                f"{s['total_deliveries']} kali",
                format_currency(s['total_amount']),
                s.get('user_name', '-'),
                s.get('notes', ''),
            ))

    def _load_courier_filter(self):
        """Load daftar kurir untuk filter"""
        try:
            names = db.get_all_courier_names()
        except Exception:
            names = []
        self.filter_courier_combo['values'] = ["Semua Kurir"] + names

    def _mark_collected(self):
        """Mark semua pending milik kurir terpilih sebagai collected (kurir langsung ambil uang)"""
        selected = self.summary_tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih kurir dari tabel ringkasan!")
            return

        values = self.summary_tree.item(selected[0], 'values')
        courier_name = values[0]

        if messagebox.askyesno("Konfirmasi",
                               f"Tandai SEMUA antaran pending milik '{courier_name}' sebagai sudah diambil?\n\n"
                               f"Artinya kurir '{courier_name}' telah mengambil uang ongkir dari setiap antaran."):
            affected = db.mark_delivery_collected_bulk(courier_name)
            if affected > 0:
                messagebox.showinfo("Berhasil", f"{affected} antaran ditandai sebagai 'Diambil' untuk kurir {courier_name}")
            else:
                messagebox.showinfo("Info", f"Tidak ada antaran pending untuk kurir {courier_name}")
            self.refresh_data()

    def _settle_courier(self):
        """Serah terima: kurir menyerahkan semua uang yang dikumpulkan ke owner"""
        selected = self.summary_tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih kurir dari tabel ringkasan!")
            return

        values = self.summary_tree.item(selected[0], 'values')
        courier_name = values[0]

        # Dialog untuk catatan
        dialog = tk.Toplevel(self)
        dialog.title("Serah Terima Uang Kurir")
        dialog.geometry("450x420")
        dialog.minsize(400, 340)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 210
        dialog.geometry(f'+{x}+{y}')

        tk.Label(dialog, text="✅ Serah Terima Uang Kurir", font=FONTS['subtitle'],
                 bg=COLORS['white'], fg=COLORS['primary_dark']).pack(side='top', pady=(20, 5))

        tk.Label(dialog, text=f"Kurir: {courier_name}", font=FONTS['heading'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(side='top', pady=(0, 15))

        # Tombol aksi di-pack di BOTTOM terlebih dahulu agar selalu terlihat
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(side='bottom', fill='x', padx=25, pady=15)

        # Hitung total yang akan disetor
        try:
            summary = db.get_courier_summary()
            courier_data = next((s for s in summary if s['courier_name'] == courier_name), None)
            if courier_data:
                collected = courier_data['collected_amount']
                count = courier_data['collected_count']
            else:
                collected = 0
                count = 0
        except Exception:
            collected = 0
            count = 0

        info_frame = tk.Frame(dialog, bg=COLORS['info_bg'], padx=15, pady=10)
        info_frame.pack(side='top', fill='x', padx=25)

        tk.Label(info_frame, text=f"Jumlah antaran: {count} kali",
                 font=FONTS['body'], bg=COLORS['info_bg'], fg=COLORS['text_dark']).pack(anchor='w')
        tk.Label(info_frame, text=f"Total uang disetor: {format_currency(collected)}",
                 font=FONTS['body_bold'], bg=COLORS['info_bg'], fg=COLORS['primary']).pack(anchor='w')

        if count == 0:
            tk.Label(dialog, text="⚠️ Tidak ada uang yang perlu diserahkan.\nTandai dulu sebagai 'Diambil'.",
                     font=FONTS['body'], bg=COLORS['white'], fg=COLORS['warning'], justify='center').pack(pady=15)
            tk.Button(btn_frame, text="OK", font=FONTS['button'], bg=COLORS['border'],
                      fg=COLORS['text_dark'], relief='flat', command=dialog.destroy, padx=30, pady=6).pack()
            return

        # Notes
        form = tk.Frame(dialog, bg=COLORS['white'], padx=25)
        form.pack(side='top', fill='both', expand=True, pady=10)

        tk.Label(form, text="Catatan (opsional):", font=FONTS['body'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 3))
        notes_var = tk.StringVar()
        notes_entry = tk.Entry(form, textvariable=notes_var, font=FONTS['input'],
                               relief='solid', bd=1, bg=COLORS['bg_light'])
        notes_entry.pack(fill='x', ipady=6)

        def process():
            note_text = notes_var.get().strip()
            count_done, total_done = db.settle_courier(courier_name, self.user['id'], note_text)
            dialog.destroy()
            self.refresh_data()

            if count_done > 0:
                # Tampilkan dialog bukti serah terima dengan tombol simpan
                res_dialog = tk.Toplevel(self)
                res_dialog.title("Bukti Serah Terima Kurir")
                res_dialog.geometry("440x440")
                res_dialog.minsize(400, 360)
                res_dialog.resizable(True, True)
                res_dialog.configure(bg=COLORS['white'])
                res_dialog.transient(self)
                res_dialog.grab_set()

                res_dialog.update_idletasks()
                rx = (res_dialog.winfo_screenwidth() // 2) - 220
                ry = (res_dialog.winfo_screenheight() // 2) - 220
                res_dialog.geometry(f'+{rx}+{ry}')

                tk.Label(res_dialog, text="✅", font=('Segoe UI', 36), bg=COLORS['white']).pack(side='top', pady=(15, 0))
                tk.Label(res_dialog, text="Serah Terima Berhasil!", font=FONTS['subtitle'],
                         bg=COLORS['white'], fg=COLORS['success']).pack(side='top')

                btn_box = tk.Frame(res_dialog, bg=COLORS['white'])
                btn_box.pack(side='bottom', fill='x', padx=25, pady=(10, 15))

                info = tk.Frame(res_dialog, bg=COLORS['bg_light'], padx=15, pady=12,
                                highlightbackground=COLORS['border_light'], highlightthickness=1)
                info.pack(side='top', fill='both', expand=True, padx=25, pady=15)

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                receiver_name = self.user.get('full_name', 'Owner')

                rows = [
                    ("Kurir:", courier_name),
                    ("Tanggal:", now_str),
                    ("Diterima Oleh:", receiver_name),
                    ("Jumlah Antaran:", f"{count_done} kali"),
                    ("Total Disetor:", format_currency(total_done)),
                ]
                if note_text:
                    rows.append(("Catatan:", note_text))

                for lbl, val in rows:
                    r = tk.Frame(info, bg=COLORS['bg_light'])
                    r.pack(fill='x', pady=2)
                    tk.Label(r, text=lbl, font=FONTS['body'], bg=COLORS['bg_light'], fg=COLORS['text_medium']).pack(side='left')
                    tk.Label(r, text=val, font=FONTS['body_bold'], bg=COLORS['bg_light'], fg=COLORS['text_dark']).pack(side='right')

                def save_proof():
                    file_path = filedialog.asksaveasfilename(
                        parent=res_dialog,
                        title="Simpan Bukti Serah Terima",
                        defaultextension=".txt",
                        initialfile=f"SerahTerima_{courier_name}_{datetime.now().strftime('%Y%m%d%H%M')}.txt",
                        filetypes=[("Text File (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
                    )
                    if not file_path:
                        return
                    try:
                        lines = [
                            "=" * 40,
                            "       BUKTI SERAH TERIMA UANG KURIR    ",
                            "=" * 40,
                            f"Kurir          : {courier_name}",
                            f"Tanggal/Waktu  : {now_str}",
                            f"Penerima       : {receiver_name}",
                            f"Jumlah Antaran : {count_done} kali",
                            f"Total Disetor  : {format_currency(total_done)}",
                        ]
                        if note_text:
                            lines.append(f"Catatan        : {note_text}")
                        lines.append("=" * 40)
                        lines.append("      Telah diterima dengan benar.      ")
                        lines.append("=" * 40)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(lines) + "\n")
                        messagebox.showinfo("Berhasil", f"Bukti berhasil disimpan di:\n{file_path}", parent=res_dialog)
                    except Exception as e:
                        messagebox.showerror("Error", f"Gagal menyimpan bukti:\n{e}", parent=res_dialog)

                save_btn = tk.Button(
                    btn_box, text="  💾  Simpan Bukti  ", font=FONTS['button'],
                    bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
                    cursor='hand2', command=save_proof, pady=8
                )
                save_btn.pack(side='left', fill='x', expand=True, padx=(0, 10))

                close_btn = tk.Button(
                    btn_box, text="  Tutup  ", font=FONTS['button'],
                    bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
                    cursor='hand2', command=res_dialog.destroy, pady=8
                )
                close_btn.pack(side='right', fill='x', expand=True)

            else:
                messagebox.showinfo("Info", "Tidak ada uang yang perlu diserahkan.")

        tk.Button(
            btn_frame, text=f"  {ICONS['check']}  Proses Serah Terima  ", font=FONTS['button'],
            bg=COLORS['success'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=process, padx=15, pady=8
        ).pack(side='left', padx=(0, 10))

        tk.Button(
            btn_frame, text="Batal", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=20, pady=8
        ).pack(side='left')

    def _mark_selected_collected(self):
        """Tandai antaran terpilih dari detail sebagai collected"""
        selected = self.detail_tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih antaran dari tabel detail!")
            return

        delivery_id = int(selected[0])

        if messagebox.askyesno("Konfirmasi",
                               f"Tandai antaran ID {delivery_id} sebagai sudah diambil kurirnya?"):
            db.mark_delivery_collected(delivery_id)
            messagebox.showinfo("Berhasil", "Antaran ditandai sebagai 'Diambil'")
            self.refresh_data()
