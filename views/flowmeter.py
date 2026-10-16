"""
View Pencatatan Flow Meter Air (Kilometer Air Awal & Akhir Shift)
Depo Air - Digitalisasi Catatan Meteran Air
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import os

from styles import COLORS, FONTS, ICONS, format_currency
import database as db

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class FlowMeterView(tk.Frame):
    """Tampilan pencatatan flow meter (kilometer air) awal dan akhir shift"""

    def __init__(self, parent, user):
        super().__init__(parent, bg=COLORS['bg_light'])
        self.user = user

        # Filter states
        self.date_from_var = tk.StringVar(value=datetime.now().replace(day=1).strftime("%Y-%m-%d"))
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.search_var = tk.StringVar()

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # ===== HEADER =====
        header = tk.Frame(self, bg=COLORS['white'], padx=25, pady=18,
                          highlightbackground=COLORS['border_light'], highlightthickness=1)
        header.pack(fill='x')

        title_frame = tk.Frame(header, bg=COLORS['white'])
        title_frame.pack(side='left')

        tk.Label(
            title_frame, text=f"{ICONS.get('flowmeter', '⏱️')}  Pencatatan Flow Meter Air",
            font=FONTS['title'], bg=COLORS['white'], fg=COLORS['primary_dark']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Catat kilometer awal & akhir shift • Hitung otomatis liter, galon (Bio 21,5L / RO 20,5L), dan omzet air",
            font=FONTS['small'], bg=COLORS['white'], fg=COLORS['text_medium']
        ).pack(anchor='w', pady=(3, 0))

        # Header Action Buttons
        btn_box = tk.Frame(header, bg=COLORS['white'])
        btn_box.pack(side='right')

        # Tombol Rekonsiliasi POS
        recon_btn = tk.Button(
            btn_box, text="  📊 Rekonsiliasi POS  ", font=FONTS['button'],
            bg=COLORS['info_bg'], fg=COLORS['primary'], relief='flat',
            cursor='hand2', command=self._show_reconciliation_dialog, pady=8, padx=10
        )
        recon_btn.pack(side='left', padx=(0, 8))

        # Tombol Unduh Excel
        excel_btn = tk.Button(
            btn_box, text=f"  💾 Unduh Excel  ", font=FONTS['button'],
            bg=COLORS['success'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._export_to_excel, pady=8, padx=12
        )
        excel_btn.pack(side='left', padx=(0, 8))
        excel_btn.bind('<Enter>', lambda e: excel_btn.config(bg='#256029'))
        excel_btn.bind('<Leave>', lambda e: excel_btn.config(bg=COLORS['success']))

        # Tombol Catat Meteran Baru
        add_btn = tk.Button(
            btn_box, text=f"  {ICONS['add']} Catat Meteran  ", font=FONTS['button'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_add_dialog, pady=8, padx=14
        )
        add_btn.pack(side='left')
        add_btn.bind('<Enter>', lambda e: add_btn.config(bg=COLORS['primary_hover']))
        add_btn.bind('<Leave>', lambda e: add_btn.config(bg=COLORS['primary']))

        # ===== SUMMARY CARDS =====
        summary = tk.Frame(self, bg=COLORS['bg_light'], padx=25, pady=12)
        summary.pack(fill='x')
        summary.columnconfigure(0, weight=1)
        summary.columnconfigure(1, weight=1)
        summary.columnconfigure(2, weight=1)
        summary.columnconfigure(3, weight=1)

        # Card 1: Air Bio Energi
        self.bio_card = tk.Frame(summary, bg=COLORS['white'], padx=18, pady=12,
                                 highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.bio_card.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        tk.Label(self.bio_card, text="🚰 Air Bio Energi (Rp 5.000)", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['primary']).pack(anchor='w')
        self.bio_liters_label = tk.Label(self.bio_card, text="0 Liter", font=FONTS['medium_number'],
                                         bg=COLORS['white'], fg=COLORS['text_dark'])
        self.bio_liters_label.pack(anchor='w', pady=(2, 0))
        self.bio_detail_label = tk.Label(self.bio_card, text="0 Galon • Rp 0", font=FONTS['small'],
                                         bg=COLORS['white'], fg=COLORS['text_medium'])
        self.bio_detail_label.pack(anchor='w')

        # Card 2: Air RO (Reverse Osmosis)
        self.ro_card = tk.Frame(summary, bg=COLORS['white'], padx=18, pady=12,
                                highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.ro_card.grid(row=0, column=1, sticky='nsew', padx=3)
        tk.Label(self.ro_card, text="💧 Air RO (Rp 10.000)", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['info']).pack(anchor='w')
        self.ro_liters_label = tk.Label(self.ro_card, text="0 Liter", font=FONTS['medium_number'],
                                        bg=COLORS['white'], fg=COLORS['text_dark'])
        self.ro_liters_label.pack(anchor='w', pady=(2, 0))
        self.ro_detail_label = tk.Label(self.ro_card, text="0 Galon • Rp 0", font=FONTS['small'],
                                        bg=COLORS['white'], fg=COLORS['text_medium'])
        self.ro_detail_label.pack(anchor='w')

        # Card 3: Total Omzet Air
        self.total_card = tk.Frame(summary, bg=COLORS['white'], padx=18, pady=12,
                                   highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.total_card.grid(row=0, column=2, sticky='nsew', padx=3)
        tk.Label(self.total_card, text="💰 Total Omzet Fisik Air", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['success']).pack(anchor='w')
        self.total_rev_label = tk.Label(self.total_card, text="Rp 0", font=FONTS['medium_number'],
                                        bg=COLORS['white'], fg=COLORS['success'])
        self.total_rev_label.pack(anchor='w', pady=(2, 0))
        self.total_gal_label = tk.Label(self.total_card, text="0 Galon (0 Liter)", font=FONTS['small'],
                                        bg=COLORS['white'], fg=COLORS['text_medium'])
        self.total_gal_label.pack(anchor='w')

        # Card 4: Status Shift Aktif
        self.shift_card = tk.Frame(summary, bg=COLORS['white'], padx=18, pady=12,
                                   highlightbackground=COLORS['border_light'], highlightthickness=1)
        self.shift_card.grid(row=0, column=3, sticky='nsew', padx=(6, 0))
        tk.Label(self.shift_card, text="⏱️ Shift & Catatan", font=FONTS['small_bold'],
                 bg=COLORS['white'], fg=COLORS['warning']).pack(anchor='w')
        self.shift_status_label = tk.Label(self.shift_card, text="Shift Tertutup", font=FONTS['heading'],
                                           bg=COLORS['white'], fg=COLORS['text_dark'])
        self.shift_status_label.pack(anchor='w', pady=(2, 0))
        self.shift_info_label = tk.Label(self.shift_card, text="Total: 0 catatan", font=FONTS['small'],
                                         bg=COLORS['white'], fg=COLORS['text_medium'])
        self.shift_info_label.pack(anchor='w')

        # ===== FILTER BAR =====
        filter_frame = tk.Frame(self, bg=COLORS['white'], padx=15, pady=8,
                                highlightbackground=COLORS['border_light'], highlightthickness=1)
        filter_frame.pack(fill='x', padx=25, pady=(0, 10))

        tk.Label(filter_frame, text="Filter:", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(side='left', padx=(0, 8))

        # Quick date buttons
        today_str = datetime.now().strftime("%Y-%m-%d")
        month_start_str = datetime.now().replace(day=1).strftime("%Y-%m-%d")

        def set_filter(f_from, f_to):
            self.date_from_var.set(f_from)
            self.date_to_var.set(f_to)
            self.refresh_data()

        tk.Button(
            filter_frame, text="Hari Ini", font=FONTS['small'], bg=COLORS['bg_light'],
            fg=COLORS['text_dark'], relief='flat', cursor='hand2',
            command=lambda: set_filter(today_str, today_str), padx=8, pady=3
        ).pack(side='left', padx=3)

        tk.Button(
            filter_frame, text="Bulan Ini", font=FONTS['small'], bg=COLORS['bg_light'],
            fg=COLORS['text_dark'], relief='flat', cursor='hand2',
            command=lambda: set_filter(month_start_str, today_str), padx=8, pady=3
        ).pack(side='left', padx=3)

        tk.Button(
            filter_frame, text="Semua", font=FONTS['small'], bg=COLORS['bg_light'],
            fg=COLORS['text_dark'], relief='flat', cursor='hand2',
            command=lambda: set_filter("", ""), padx=8, pady=3
        ).pack(side='left', padx=3)

        tk.Label(filter_frame, text="   Dari:", font=FONTS['body'],
                 bg=COLORS['white'], fg=COLORS['text_medium']).pack(side='left', padx=(10, 5))

        tk.Entry(filter_frame, textvariable=self.date_from_var, font=FONTS['small'],
                 width=11, relief='solid', bd=1).pack(side='left')

        tk.Label(filter_frame, text=" s/d:", font=FONTS['body'],
                 bg=COLORS['white'], fg=COLORS['text_medium']).pack(side='left', padx=5)

        tk.Entry(filter_frame, textvariable=self.date_to_var, font=FONTS['small'],
                 width=11, relief='solid', bd=1).pack(side='left')

        tk.Label(filter_frame, text="  Cari:", font=FONTS['body'],
                 bg=COLORS['white'], fg=COLORS['text_medium']).pack(side='left', padx=(15, 5))

        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, font=FONTS['small'],
                                width=16, relief='solid', bd=1)
        search_entry.pack(side='left')
        search_entry.bind('<Return>', lambda e: self.refresh_data())

        filter_btn = tk.Button(
            filter_frame, text=f"  {ICONS['search']} Terapkan  ", font=FONTS['small_bold'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self.refresh_data, padx=10, pady=3
        )
        filter_btn.pack(side='left', padx=8)

        reset_btn = tk.Button(
            filter_frame, text="Reset", font=FONTS['small'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=self._reset_filter, padx=8, pady=3
        )
        reset_btn.pack(side='left')

        # ===== ACTION FRAME BOTTOM (Pack FIRST at bottom to prevent clipping) =====
        action_frame = tk.Frame(self, bg=COLORS['bg_light'], pady=5)
        action_frame.pack(side='bottom', fill='x', padx=25, pady=(5, 12))

        # Edit button
        edit_btn = tk.Button(
            action_frame, text=f"  {ICONS['edit']} Edit Catatan  ", font=FONTS['body_bold'],
            bg=COLORS['primary_light'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_edit_dialog, pady=8, padx=12
        )
        edit_btn.pack(side='left', padx=(0, 8))

        # Close shift button
        self.close_shift_btn = tk.Button(
            action_frame, text="  🏁 Tutup Shift / Meter Akhir  ", font=FONTS['body_bold'],
            bg=COLORS['warning'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._show_close_shift_dialog, pady=8, padx=12
        )
        self.close_shift_btn.pack(side='left', padx=(0, 8))

        # Delete button
        del_btn = tk.Button(
            action_frame, text=f"  {ICONS['delete']} Hapus  ", font=FONTS['body_bold'],
            bg=COLORS['danger'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=self._delete_record, pady=8, padx=12
        )
        del_btn.pack(side='left', padx=(0, 8))

        self.count_label = tk.Label(
            action_frame, text="", font=FONTS['small'],
            bg=COLORS['bg_light'], fg=COLORS['text_medium']
        )
        self.count_label.pack(side='right')

        # ===== TABLE FRAME =====
        table_frame = tk.Frame(self, bg=COLORS['white'],
                               highlightbackground=COLORS['border_light'], highlightthickness=1)
        table_frame.pack(fill='both', expand=True, padx=25, pady=(0, 5))

        columns = (
            'id', 'date', 'shift', 'user',
            'bio_start', 'bio_end', 'bio_liters', 'bio_gallons', 'bio_revenue',
            'ro_start', 'ro_end', 'ro_liters', 'ro_gallons', 'ro_revenue',
            'total_revenue', 'status', 'notes'
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')

        # Headings & Column config
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Tanggal')
        self.tree.heading('shift', text='Shift')
        self.tree.heading('user', text='Petugas')
        self.tree.heading('bio_start', text='Bio Awal')
        self.tree.heading('bio_end', text='Bio Akhir')
        self.tree.heading('bio_liters', text='Bio (L)')
        self.tree.heading('bio_gallons', text='Bio (Galon)')
        self.tree.heading('bio_revenue', text='Bio (Rp)')
        self.tree.heading('ro_start', text='RO Awal')
        self.tree.heading('ro_end', text='RO Akhir')
        self.tree.heading('ro_liters', text='RO (L)')
        self.tree.heading('ro_gallons', text='RO (Galon)')
        self.tree.heading('ro_revenue', text='RO (Rp)')
        self.tree.heading('total_revenue', text='Total Omzet')
        self.tree.heading('status', text='Status')
        self.tree.heading('notes', text='Catatan')

        self.tree.column('id', width=45, anchor='center')
        self.tree.column('date', width=90, anchor='center')
        self.tree.column('shift', width=80, anchor='center')
        self.tree.column('user', width=95, anchor='w')
        self.tree.column('bio_start', width=75, anchor='e')
        self.tree.column('bio_end', width=75, anchor='e')
        self.tree.column('bio_liters', width=75, anchor='e')
        self.tree.column('bio_gallons', width=80, anchor='e')
        self.tree.column('bio_revenue', width=90, anchor='e')
        self.tree.column('ro_start', width=75, anchor='e')
        self.tree.column('ro_end', width=75, anchor='e')
        self.tree.column('ro_liters', width=75, anchor='e')
        self.tree.column('ro_gallons', width=75, anchor='e')
        self.tree.column('ro_revenue', width=90, anchor='e')
        self.tree.column('total_revenue', width=105, anchor='e')
        self.tree.column('status', width=70, anchor='center')
        self.tree.column('notes', width=120, anchor='w')

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')

        self.tree.bind('<Double-1>', lambda e: self._show_edit_dialog())

        # Tag styles
        self.tree.tag_configure('open_shift', background='#FFF9C4')  # Kuning lembut untuk shift terbuka

    def _reset_filter(self):
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.search_var.set("")
        self.refresh_data()

    def refresh_data(self):
        """Memuat ulang data dari database ke tampilan tabel & kartu ringkasan"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        d_from = self.date_from_var.get().strip() or None
        d_to = self.date_to_var.get().strip() or None
        search = self.search_var.get().strip() or None

        records = db.get_water_meters(d_from, d_to, search)
        summary = db.get_water_meter_summary(d_from, d_to)
        open_shift = db.get_open_water_meter_shift()

        # Update KPI cards
        self.bio_liters_label.config(text=f"{summary['total_bio_liters']:,.1f} L".replace(',', '.'))
        self.bio_detail_label.config(text=f"{summary['total_bio_gallons']:,.1f} Galon • {format_currency(summary['total_bio_revenue'])}")

        self.ro_liters_label.config(text=f"{summary['total_ro_liters']:,.1f} L".replace(',', '.'))
        self.ro_detail_label.config(text=f"{summary['total_ro_gallons']:,.1f} Galon • {format_currency(summary['total_ro_revenue'])}")

        self.total_rev_label.config(text=format_currency(summary['total_revenue']))
        self.total_gal_label.config(text=f"{summary['total_gallons']:,.1f} Galon ({summary['total_liters']:,.1f} Liter)")

        if open_shift:
            self.shift_status_label.config(text="⚠️ Shift Terbuka", fg=COLORS['warning'])
            self.shift_info_label.config(text=f"{open_shift['shift_name']} ({open_shift['record_date']})")
        else:
            self.shift_status_label.config(text="✅ Shift Ditutup", fg=COLORS['success'])
            self.shift_info_label.config(text=f"Total: {len(records)} catatan")

        self.count_label.config(text=f"Menampilkan: {len(records)} catatan flow meter")

        for r in records:
            status_text = "Buka" if r['status'] == 'open' else "Selesai"
            tag = 'open_shift' if r['status'] == 'open' else ''

            self.tree.insert('', 'end', values=(
                r['id'],
                r['record_date'],
                r['shift_name'],
                r['user_name'] or '-',
                f"{r['bio_meter_start']:,.1f}".replace(',', '.'),
                f"{r['bio_meter_end']:,.1f}".replace(',', '.') if r['status'] == 'closed' else '-',
                f"{r['bio_liters']:,.1f}".replace(',', '.') if r['status'] == 'closed' else '-',
                f"{r['bio_gallons']:,.2f}".replace(',', '.') if r['status'] == 'closed' else '-',
                format_currency(r['bio_revenue']) if r['status'] == 'closed' else '-',
                f"{r['ro_meter_start']:,.1f}".replace(',', '.'),
                f"{r['ro_meter_end']:,.1f}".replace(',', '.') if r['status'] == 'closed' else '-',
                f"{r['ro_liters']:,.1f}".replace(',', '.') if r['status'] == 'closed' else '-',
                f"{r['ro_gallons']:,.2f}".replace(',', '.') if r['status'] == 'closed' else '-',
                format_currency(r['ro_revenue']) if r['status'] == 'closed' else '-',
                format_currency(r['total_revenue']) if r['status'] == 'closed' else '-',
                status_text,
                r['notes'] or '-'
            ), tags=(tag,) if tag else ())

    # ==================== DIALOG INPUT & EDIT ====================

    def _show_add_dialog(self):
        """Dialog untuk mencatat meteran baru"""
        self._open_meter_form_dialog("Catat Flow Meter Air Baru")

    def _show_edit_dialog(self):
        """Dialog untuk mengedit catatan meteran yang dipilih"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih baris meteran yang ingin diedit!")
            return
        meter_id = self.tree.item(selected[0])['values'][0]
        rec = db.get_water_meter_by_id(meter_id)
        if not rec:
            messagebox.showerror("Error", "Data tidak ditemukan!")
            return
        self._open_meter_form_dialog(f"Edit Flow Meter (ID: {meter_id})", existing_data=rec)

    def _show_close_shift_dialog(self):
        """Pintasan untuk menutup shift yang berstatus 'open' atau baris terpilih"""
        selected = self.tree.selection()
        if selected:
            meter_id = self.tree.item(selected[0])['values'][0]
            rec = db.get_water_meter_by_id(meter_id)
        else:
            rec = db.get_open_water_meter_shift()

        if not rec:
            messagebox.showinfo("Info", "Tidak ada shift terbuka yang perlu ditutup.\nSilakan pilih baris meteran yang ingin ditutup.")
            return

        self._open_meter_form_dialog(f"Tutup Shift & Masukkan Meter Akhir ({rec['shift_name']})", existing_data=rec, is_closing_only=True)

    def _open_meter_form_dialog(self, title, existing_data=None, is_closing_only=False):
        """Dialog formulir pengisian flow meter dengan kalkulasi live"""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("540x680")
        dialog.minsize(480, 520)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 270
        y = (dialog.winfo_screenheight() // 2) - 340
        dialog.geometry(f'+{x}+{y}')

        # Header
        tk.Label(dialog, text=title, font=FONTS['subtitle'],
                 bg=COLORS['white'], fg=COLORS['primary_dark']).pack(side='top', pady=(15, 6))

        sep = tk.Frame(dialog, bg=COLORS['accent_light'], height=2)
        sep.pack(side='top', fill='x', padx=25)

        # Tombol aksi di-pack di BOTTOM terlebih dahulu agar selalu terlihat
        btn_frame = tk.Frame(dialog, bg=COLORS['white'])
        btn_frame.pack(side='bottom', fill='x', padx=25, pady=15)

        # Body form dalam scrollable / pack container
        form = tk.Frame(dialog, bg=COLORS['white'], padx=25)
        form.pack(side='top', fill='both', expand=True, pady=10)

        # Nilai awal / default
        latest = db.get_latest_water_meter()

        def_date = existing_data['record_date'] if existing_data else date.today().strftime("%Y-%m-%d")
        def_shift = existing_data['shift_name'] if existing_data else "Shift 1"
        def_user = existing_data['user_name'] if existing_data else self.user.get('full_name', 'Kasir')

        def_bio_start = str(existing_data['bio_meter_start']) if existing_data else (str(latest['bio_meter_end']) if latest else "0")
        def_bio_end = str(existing_data['bio_meter_end']) if existing_data and existing_data['bio_meter_end'] > 0 else ""

        def_ro_start = str(existing_data['ro_meter_start']) if existing_data else (str(latest['ro_meter_end']) if latest else "0")
        def_ro_end = str(existing_data['ro_meter_end']) if existing_data and existing_data['ro_meter_end'] > 0 else ""

        def_notes = existing_data['notes'] if existing_data else ""
        def_status = existing_data['status'] if existing_data else "closed"

        # --- Row 1: Tanggal, Shift, Petugas ---
        top_row = tk.Frame(form, bg=COLORS['white'])
        top_row.pack(fill='x', pady=(0, 10))

        # Tanggal
        t_col1 = tk.Frame(top_row, bg=COLORS['white'])
        t_col1.pack(side='left', fill='x', expand=True, padx=(0, 6))
        tk.Label(t_col1, text="Tanggal", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w')
        date_var = tk.StringVar(value=def_date)
        tk.Entry(t_col1, textvariable=date_var, font=FONTS['input'], relief='solid', bd=1, bg=COLORS['bg_light']).pack(fill='x', ipady=4)

        # Shift
        t_col2 = tk.Frame(top_row, bg=COLORS['white'])
        t_col2.pack(side='left', fill='x', expand=True, padx=3)
        tk.Label(t_col2, text="Shift / Sesi", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w')
        shift_var = tk.StringVar(value=def_shift)
        shift_combo = ttk.Combobox(t_col2, textvariable=shift_var, font=FONTS['input'],
                                   values=["Shift 1", "Shift 2", "Harian", "Shift Pagi", "Shift Sore"])
        shift_combo.pack(fill='x', ipady=3)

        # Petugas
        t_col3 = tk.Frame(top_row, bg=COLORS['white'])
        t_col3.pack(side='left', fill='x', expand=True, padx=(6, 0))
        tk.Label(t_col3, text="Petugas", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w')
        user_var = tk.StringVar(value=def_user)
        tk.Entry(t_col3, textvariable=user_var, font=FONTS['input'], relief='solid', bd=1, bg=COLORS['bg_light']).pack(fill='x', ipady=4)

        # --- Card 1: Air Bio Energi ---
        bio_box = tk.LabelFrame(form, text="  🚰 Air Bio Energi (Rp 5.000 / 21,5 Liter)  ",
                                font=FONTS['body_bold'], fg=COLORS['primary_dark'], bg=COLORS['white'],
                                padx=12, pady=8, bd=1, relief='solid')
        bio_box.pack(fill='x', pady=(0, 10))

        b_row = tk.Frame(bio_box, bg=COLORS['white'])
        b_row.pack(fill='x')

        # Bio Meter Awal
        b_col1 = tk.Frame(b_row, bg=COLORS['white'])
        b_col1.pack(side='left', fill='x', expand=True, padx=(0, 6))
        tk.Label(b_col1, text="Meter Awal (L):", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_medium']).pack(anchor='w')
        bio_start_var = tk.StringVar(value=def_bio_start)
        bio_start_entry = tk.Entry(b_col1, textvariable=bio_start_var, font=('Segoe UI', 12, 'bold'),
                                   relief='solid', bd=1, bg=COLORS['bg_light'], justify='right')
        bio_start_entry.pack(fill='x', ipady=4)

        # Bio Meter Akhir
        b_col2 = tk.Frame(b_row, bg=COLORS['white'])
        b_col2.pack(side='left', fill='x', expand=True, padx=(6, 0))
        tk.Label(b_col2, text="Meter Akhir (L):", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['primary']).pack(anchor='w')
        bio_end_var = tk.StringVar(value=def_bio_end)
        bio_end_entry = tk.Entry(b_col2, textvariable=bio_end_var, font=('Segoe UI', 12, 'bold'),
                                 relief='solid', bd=1, bg='#E8F5E9', justify='right')
        bio_end_entry.pack(fill='x', ipady=4)

        # Bio Live Feedback
        bio_calc_label = tk.Label(bio_box, text="Liter Keluar: 0 L  •  Galon: 0 galon  •  Omzet: Rp 0",
                                  font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['primary'])
        bio_calc_label.pack(anchor='w', pady=(6, 0))

        # --- Card 2: Air RO (Reverse Osmosis) ---
        ro_box = tk.LabelFrame(form, text="  💧 Air RO (Reverse Osmosis) (Rp 10.000 / 20,5 Liter)  ",
                               font=FONTS['body_bold'], fg=COLORS['info'], bg=COLORS['white'],
                               padx=12, pady=8, bd=1, relief='solid')
        ro_box.pack(fill='x', pady=(0, 10))

        r_row = tk.Frame(ro_box, bg=COLORS['white'])
        r_row.pack(fill='x')

        # RO Meter Awal
        r_col1 = tk.Frame(r_row, bg=COLORS['white'])
        r_col1.pack(side='left', fill='x', expand=True, padx=(0, 6))
        tk.Label(r_col1, text="Meter Awal (L):", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_medium']).pack(anchor='w')
        ro_start_var = tk.StringVar(value=def_ro_start)
        ro_start_entry = tk.Entry(r_col1, textvariable=ro_start_var, font=('Segoe UI', 12, 'bold'),
                                  relief='solid', bd=1, bg=COLORS['bg_light'], justify='right')
        ro_start_entry.pack(fill='x', ipady=4)

        # RO Meter Akhir
        r_col2 = tk.Frame(r_row, bg=COLORS['white'])
        r_col2.pack(side='left', fill='x', expand=True, padx=(6, 0))
        tk.Label(r_col2, text="Meter Akhir (L):", font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['info']).pack(anchor='w')
        ro_end_var = tk.StringVar(value=def_ro_end)
        ro_end_entry = tk.Entry(r_col2, textvariable=ro_end_var, font=('Segoe UI', 12, 'bold'),
                                relief='solid', bd=1, bg='#E8F5E9', justify='right')
        ro_end_entry.pack(fill='x', ipady=4)

        # RO Live Feedback
        ro_calc_label = tk.Label(ro_box, text="Liter Keluar: 0 L  •  Galon: 0 galon  •  Omzet: Rp 0",
                                 font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['info'])
        ro_calc_label.pack(anchor='w', pady=(6, 0))

        # --- Card 3: Ringkasan Total Real-Time ---
        sum_box = tk.Frame(form, bg=COLORS['info_bg'], padx=12, pady=8,
                           highlightbackground=COLORS['border_light'], highlightthickness=1)
        sum_box.pack(fill='x', pady=(0, 10))

        tk.Label(sum_box, text="📊 Total Gabungan Real-Time:", font=FONTS['small_bold'],
                 bg=COLORS['info_bg'], fg=COLORS['primary_dark']).pack(anchor='w')
        total_live_label = tk.Label(sum_box, text="Total: 0 Liter  •  0 Galon  •  Omzet: Rp 0",
                                    font=FONTS['body_bold'], bg=COLORS['info_bg'], fg=COLORS['success'])
        total_live_label.pack(anchor='w', pady=(2, 0))

        # --- Catatan ---
        tk.Label(form, text="Catatan (opsional, misal: cuci filter, bilas galon, dll):",
                 font=FONTS['small_bold'], bg=COLORS['white'], fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 2))
        notes_var = tk.StringVar(value=def_notes)
        notes_entry = tk.Entry(form, textvariable=notes_var, font=FONTS['input'],
                               relief='solid', bd=1, bg=COLORS['bg_light'])
        notes_entry.pack(fill='x', ipady=4)

        # Live calculation callback
        def recalculate(*args):
            try:
                b_start = float(bio_start_var.get().replace(',', '.') or 0)
                b_end = float(bio_end_var.get().replace(',', '.') or 0) if bio_end_var.get().strip() else b_start
                r_start = float(ro_start_var.get().replace(',', '.') or 0)
                r_end = float(ro_end_var.get().replace(',', '.') or 0) if ro_end_var.get().strip() else r_start

                b_liters = max(0.0, round(b_end - b_start, 2)) if bio_end_var.get().strip() else 0.0
                b_gal = round(b_liters / 21.5, 2)
                b_rev = round(b_gal * 5000)

                r_liters = max(0.0, round(r_end - r_start, 2)) if ro_end_var.get().strip() else 0.0
                r_gal = round(r_liters / 20.5, 2)
                r_rev = round(r_gal * 10000)

                tot_liters = round(b_liters + r_liters, 2)
                tot_gal = round(b_gal + r_gal, 2)
                tot_rev = b_rev + r_rev

                bio_calc_label.config(
                    text=f"Liter Keluar: {b_liters:,.1f} L  •  {b_gal:,.2f} Galon  •  {format_currency(b_rev)}"
                )
                ro_calc_label.config(
                    text=f"Liter Keluar: {r_liters:,.1f} L  •  {r_gal:,.2f} Galon  •  {format_currency(r_rev)}"
                )
                total_live_label.config(
                    text=f"Total: {tot_liters:,.1f} Liter  •  {tot_gal:,.2f} Galon  •  {format_currency(tot_rev)}"
                )
            except ValueError:
                pass

        bio_start_var.trace_add('write', recalculate)
        bio_end_var.trace_add('write', recalculate)
        ro_start_var.trace_add('write', recalculate)
        ro_end_var.trace_add('write', recalculate)
        recalculate()

        # Fokus input
        if is_closing_only or (existing_data and existing_data['status'] == 'open'):
            bio_end_entry.focus_set()
        else:
            bio_start_entry.focus_set()

        # Save Handler
        def save():
            try:
                rec_date = date_var.get().strip()
                s_name = shift_var.get().strip() or "Shift 1"
                u_name = user_var.get().strip() or self.user.get('full_name', 'Kasir')
                notes_text = notes_var.get().strip()

                if not rec_date:
                    messagebox.showwarning("Peringatan", "Tanggal harus diisi!", parent=dialog)
                    return

                b_start = float(bio_start_var.get().replace(',', '.') or 0)
                r_start = float(ro_start_var.get().replace(',', '.') or 0)

                has_end = bool(bio_end_var.get().strip() and ro_end_var.get().strip())
                status = 'closed' if has_end else 'open'

                b_end = float(bio_end_var.get().replace(',', '.') or b_start)
                r_end = float(ro_end_var.get().replace(',', '.') or r_start)

                if has_end:
                    if b_end < b_start:
                        if not messagebox.askyesno(
                            "Konfirmasi Angka Meteran",
                            f"Meter akhir Bio ({b_end}) lebih kecil dari meter awal ({b_start}).\nApakah meteran sempat reset/rollover?",
                            parent=dialog
                        ):
                            return
                    if r_end < r_start:
                        if not messagebox.askyesno(
                            "Konfirmasi Angka Meteran",
                            f"Meter akhir RO ({r_end}) lebih kecil dari meter awal ({r_start}).\nApakah meteran sempat reset/rollover?",
                            parent=dialog
                        ):
                            return

                if existing_data:
                    db.update_water_meter(
                        existing_data['id'], rec_date, s_name, u_name,
                        b_start, b_end, r_start, r_end,
                        bio_lpg=21.5, bio_price=5000.0, ro_lpg=20.5, ro_price=10000.0,
                        status=status, notes=notes_text
                    )
                    messagebox.showinfo("Berhasil", "Data flow meter berhasil diperbarui!", parent=dialog)
                else:
                    db.add_water_meter(
                        rec_date, s_name, self.user.get('id', 1), u_name,
                        b_start, b_end, r_start, r_end,
                        bio_lpg=21.5, bio_price=5000.0, ro_lpg=20.5, ro_price=10000.0,
                        status=status, notes=notes_text
                    )
                    messagebox.showinfo("Berhasil", "Catatan flow meter berhasil disimpan!", parent=dialog)

                dialog.destroy()
                self.refresh_data()

            except ValueError:
                messagebox.showerror("Error", "Pastikan angka kilometer air berupa angka valid (contoh: 12975.8)!", parent=dialog)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan:\n{e}", parent=dialog)

        # Action buttons
        save_btn = tk.Button(
            btn_frame, text="  💾  Simpan Catatan  ", font=FONTS['button'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=save, padx=22, pady=9
        )
        save_btn.pack(side='left', padx=(0, 10))
        save_btn.bind('<Enter>', lambda e: save_btn.config(bg=COLORS['primary_hover']))
        save_btn.bind('<Leave>', lambda e: save_btn.config(bg=COLORS['primary']))

        cancel_btn = tk.Button(
            btn_frame, text="  Batal  ", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=20, pady=9
        )
        cancel_btn.pack(side='left')

    def _delete_record(self):
        """Hapus catatan meteran yang dipilih"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Pilih baris meteran yang ingin dihapus!")
            return

        values = self.tree.item(selected[0])['values']
        meter_id = values[0]
        rec_date = values[1]
        shift = values[2]

        if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus catatan meteran:\nTanggal: {rec_date} ({shift})?"):
            db.delete_water_meter(meter_id)
            messagebox.showinfo("Berhasil", "Catatan flow meter berhasil dihapus!")
            self.refresh_data()

    # ==================== REKONSILIASI DENGAN PENJUALAN KASIR POS ====================

    def _show_reconciliation_dialog(self):
        """Dialog rekonsiliasi antara fisik meteran air dengan transaksi kasir (POS)"""
        selected = self.tree.selection()
        if selected:
            init_date = str(self.tree.item(selected[0])['values'][1])
        else:
            init_date = date.today().strftime("%Y-%m-%d")

        dialog = tk.Toplevel(self)
        dialog.title("Rekonsiliasi Fisik Meteran Air vs Penjualan Kasir POS")
        dialog.geometry("620x560")
        dialog.minsize(540, 480)
        dialog.resizable(True, True)
        dialog.configure(bg=COLORS['white'])
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 310
        y = (dialog.winfo_screenheight() // 2) - 280
        dialog.geometry(f'+{x}+{y}')

        # Header
        tk.Label(dialog, text="📊 Rekonsiliasi Fisik Air vs Kasir (POS)",
                 font=FONTS['subtitle'], bg=COLORS['white'], fg=COLORS['primary_dark']).pack(side='top', pady=(15, 4))
        tk.Label(dialog, text="Bandingkan galon fisik yang dipompa flow meter dengan galon yang dijual kasir di komputer",
                 font=FONTS['small'], bg=COLORS['white'], fg=COLORS['text_medium']).pack(side='top', pady=(0, 10))

        sep = tk.Frame(dialog, bg=COLORS['border_light'], height=1)
        sep.pack(side='top', fill='x', padx=25)

        # Tombol aksi di-pack di BOTTOM
        btn_box = tk.Frame(dialog, bg=COLORS['white'])
        btn_box.pack(side='bottom', fill='x', padx=25, pady=15)

        # Date picker row
        date_bar = tk.Frame(dialog, bg=COLORS['white'], padx=25, pady=10)
        date_bar.pack(side='top', fill='x')

        tk.Label(date_bar, text="Pilih Tanggal Rekonsiliasi:", font=FONTS['body_bold'],
                 bg=COLORS['white'], fg=COLORS['text_dark']).pack(side='left', padx=(0, 8))

        recon_date_var = tk.StringVar(value=init_date)
        d_entry = tk.Entry(date_bar, textvariable=recon_date_var, font=FONTS['input'], width=14, relief='solid', bd=1)
        d_entry.pack(side='left')

        # Content Frame
        result_frame = tk.Frame(dialog, bg=COLORS['white'], padx=25)
        result_frame.pack(side='top', fill='both', expand=True, pady=5)

        def update_recon():
            for widget in result_frame.winfo_children():
                widget.destroy()

            t_date = recon_date_var.get().strip()
            data = db.get_water_meter_reconciliation(t_date)

            meter = data['meter']
            pos = data['pos']
            diff = data['diff']

            # Grid Container
            grid_card = tk.Frame(result_frame, bg=COLORS['bg_light'], padx=15, pady=12,
                                 highlightbackground=COLORS['border_light'], highlightthickness=1)
            grid_card.pack(fill='both', expand=True)

            # Table Header
            headers = ["Jenis Air", "Fisik Meteran", "Kasir POS", "Selisih Galon", "Selisih Uang (Rp)"]
            h_row = tk.Frame(grid_card, bg=COLORS['primary_dark'])
            h_row.pack(fill='x', pady=(0, 6))

            for h in headers:
                tk.Label(h_row, text=h, font=FONTS['small_bold'], bg=COLORS['primary_dark'],
                         fg=COLORS['text_white'], pady=6, width=15).pack(side='left', expand=True)

            # Row 1: Bio Energi
            b_diff_color = COLORS['success'] if diff['bio_qty'] >= 0 else COLORS['danger']
            r1 = tk.Frame(grid_card, bg=COLORS['white'], padx=8, pady=8, highlightbackground=COLORS['border_light'], highlightthickness=1)
            r1.pack(fill='x', pady=3)
            tk.Label(r1, text="🚰 Air Bio (5k)", font=FONTS['body_bold'], bg=COLORS['white'], width=15, anchor='w').pack(side='left', expand=True)
            tk.Label(r1, text=f"{meter['meter_bio_gallons']:,.1f} Gal ({format_currency(meter['meter_bio_revenue'])})",
                     font=FONTS['small'], bg=COLORS['white'], width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r1, text=f"{pos['bio_qty']} Gal ({format_currency(pos['bio_sales'])})",
                     font=FONTS['small'], bg=COLORS['white'], width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r1, text=f"{diff['bio_qty']:+,.1f} Gal", font=FONTS['body_bold'], bg=COLORS['white'],
                     fg=b_diff_color, width=14, anchor='center').pack(side='left', expand=True)
            tk.Label(r1, text=format_currency(diff['bio_sales']), font=FONTS['body_bold'], bg=COLORS['white'],
                     fg=b_diff_color, width=15, anchor='e').pack(side='left', expand=True)

            # Row 2: Air RO
            ro_diff_color = COLORS['success'] if diff['ro_qty'] >= 0 else COLORS['danger']
            r2 = tk.Frame(grid_card, bg=COLORS['white'], padx=8, pady=8, highlightbackground=COLORS['border_light'], highlightthickness=1)
            r2.pack(fill='x', pady=3)
            tk.Label(r2, text="💧 Air RO (10k)", font=FONTS['body_bold'], bg=COLORS['white'], width=15, anchor='w').pack(side='left', expand=True)
            tk.Label(r2, text=f"{meter['meter_ro_gallons']:,.1f} Gal ({format_currency(meter['meter_ro_revenue'])})",
                     font=FONTS['small'], bg=COLORS['white'], width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r2, text=f"{pos['ro_qty']} Gal ({format_currency(pos['ro_sales'])})",
                     font=FONTS['small'], bg=COLORS['white'], width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r2, text=f"{diff['ro_qty']:+,.1f} Gal", font=FONTS['body_bold'], bg=COLORS['white'],
                     fg=ro_diff_color, width=14, anchor='center').pack(side='left', expand=True)
            tk.Label(r2, text=format_currency(diff['ro_sales']), font=FONTS['body_bold'], bg=COLORS['white'],
                     fg=ro_diff_color, width=15, anchor='e').pack(side='left', expand=True)

            # Row 3: Total Omzet
            tot_color = COLORS['success'] if diff['total_sales'] >= 0 else COLORS['danger']
            r3 = tk.Frame(grid_card, bg='#E3F2FD', padx=8, pady=10, highlightbackground=COLORS['primary'], highlightthickness=1)
            r3.pack(fill='x', pady=(6, 0))
            tk.Label(r3, text="TOTAL OMZET", font=FONTS['body_bold'], bg='#E3F2FD', fg=COLORS['primary_dark'], width=15, anchor='w').pack(side='left', expand=True)
            tk.Label(r3, text=format_currency(meter['meter_total_revenue']), font=FONTS['body_bold'], bg='#E3F2FD', width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r3, text=format_currency(pos['total_sales']), font=FONTS['body_bold'], bg='#E3F2FD', width=16, anchor='center').pack(side='left', expand=True)
            tk.Label(r3, text="-", font=FONTS['body_bold'], bg='#E3F2FD', width=14, anchor='center').pack(side='left', expand=True)
            tk.Label(r3, text=format_currency(diff['total_sales']), font=FONTS['heading'], bg='#E3F2FD',
                     fg=tot_color, width=15, anchor='e').pack(side='left', expand=True)

            # Penjelasan
            info_text = (
                "💡 Keterangan Selisih:\n"
                "• Selisih (+) Positif : Penjualan di kasir lebih banyak dari meteran fisik.\n"
                "• Selisih (-) Negatif : Air keluar fisik dari mesin lebih banyak dari yang diinput kasir "
                "(bisa terjadi karena bilas galon, buang air kotor, atau ada transaksi belum diinput kasir)."
            )
            tk.Label(result_frame, text=info_text, font=FONTS['small'], bg=COLORS['white'],
                     fg=COLORS['text_medium'], justify='left').pack(anchor='w', pady=(10, 0))

        check_btn = tk.Button(
            date_bar, text="  🔍 Cek Rekonsiliasi  ", font=FONTS['small_bold'],
            bg=COLORS['primary'], fg=COLORS['text_white'], relief='flat',
            cursor='hand2', command=update_recon, padx=10, pady=3
        )
        check_btn.pack(side='left', padx=8)

        close_btn = tk.Button(
            btn_box, text="  Tutup  ", font=FONTS['button'],
            bg=COLORS['border'], fg=COLORS['text_dark'], relief='flat',
            cursor='hand2', command=dialog.destroy, padx=25, pady=8
        )
        close_btn.pack(side='left')

        update_recon()

    # ==================== EKSPOR EXCEL ====================

    def _export_to_excel(self):
        """Ekspor data flow meter ke file Excel (.xlsx) dengan format rapi persis seperti sheet user"""
        if not HAS_OPENPYXL:
            messagebox.showerror("Error", "Library openpyxl belum terinstal di sistem!")
            return

        d_from = self.date_from_var.get().strip() or None
        d_to = self.date_to_var.get().strip() or None
        search = self.search_var.get().strip() or None

        records = db.get_water_meters(d_from, d_to, search, limit=1000)
        if not records:
            messagebox.showinfo("Info", "Tidak ada data flow meter untuk diunduh.")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Unduh Catatan Flow Meter ke Excel",
            defaultextension=".xlsx",
            initialfile=f"Catatan_Flow_Meter_Air_{datetime.now().strftime('%Y%m%d')}.xlsx",
            filetypes=[("Excel Workbook (*.xlsx)", "*.xlsx"), ("All Files (*.*)", "*.*")]
        )
        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Flow Meter Air"

            # Title block
            ws.append(["LAPORAN PENCATATAN FLOW METER AIR - DEPO AIR"])
            ws.append([f"Periode: {d_from or 'Semua'} s/d {d_to or 'Hari ini'}  |  Diunduh: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
            ws.append([])

            # Header Row 1 (Grouped)
            # Kolom:
            # 1: No, 2: Tanggal, 3: Shift, 4: Petugas
            # 5-8: Flow Meter Bio (Awal, Akhir, Liter, Galon, Omzet Rp)
            # 9-12: Flow Meter RO (Awal, Akhir, Liter, Galon, Omzet Rp)
            # 13-15: Total Gabungan (Total Liter, Total Galon, Total Omzet Rp)
            # 16: Catatan
            row4 = ["No", "Tanggal", "Shift", "Petugas",
                    "Flow Meter Bio", "", "", "", "",
                    "Flow Meter RO", "", "", "", "",
                    "Total Gabungan", "", "", "Catatan"]
            ws.append(row4)

            row5 = ["", "", "", "",
                    "Awal (L)", "Akhir (L)", "Liter Air", "Galon (21,5L)", "Omzet Bio (Rp)",
                    "Awal (L)", "Akhir (L)", "Liter Air", "Galon (20,5L)", "Omzet RO (Rp)",
                    "Total Liter", "Total Galon", "Total Omzet (Rp)", ""]
            ws.append(row5)

            # Styling Headers
            header_fill_blue = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")
            header_fill_bio = PatternFill(start_color="1976D2", end_color="1976D2", fill_type="solid")
            header_fill_ro = PatternFill(start_color="0288D1", end_color="0288D1", fill_type="solid")
            header_fill_tot = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
            header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
            thin_border = Border(
                left=Side(style='thin', color="CCCCCC"),
                right=Side(style='thin', color="CCCCCC"),
                top=Side(style='thin', color="CCCCCC"),
                bottom=Side(style='thin', color="CCCCCC")
            )

            # Apply fill & font to header rows
            for c_idx in range(1, 19):
                cell1 = ws.cell(row=4, column=c_idx)
                cell2 = ws.cell(row=5, column=c_idx)
                cell1.font = header_font
                cell2.font = header_font
                cell1.alignment = Alignment(horizontal='center', vertical='center')
                cell2.alignment = Alignment(horizontal='center', vertical='center')

                if c_idx <= 4 or c_idx == 18:
                    cell1.fill = header_fill_blue
                    cell2.fill = header_fill_blue
                elif 5 <= c_idx <= 9:
                    cell1.fill = header_fill_bio
                    cell2.fill = header_fill_bio
                elif 10 <= c_idx <= 14:
                    cell1.fill = header_fill_ro
                    cell2.fill = header_fill_ro
                else:
                    cell1.fill = header_fill_tot
                    cell2.fill = header_fill_tot

            # Merge grouped headers
            ws.merge_cells('A4:A5')
            ws.merge_cells('B4:B5')
            ws.merge_cells('C4:C5')
            ws.merge_cells('D4:D5')
            ws.merge_cells('E4:I4')
            ws.merge_cells('J4:N4')
            ws.merge_cells('O4:Q4')
            ws.merge_cells('R4:R5')

            # Populate data
            tot_b_lit = 0
            tot_b_gal = 0
            tot_b_rev = 0
            tot_r_lit = 0
            tot_r_gal = 0
            tot_r_rev = 0
            tot_all_lit = 0
            tot_all_gal = 0
            tot_all_rev = 0

            for i, r in enumerate(reversed(records), 1):
                tot_b_lit += r['bio_liters']
                tot_b_gal += r['bio_gallons']
                tot_b_rev += r['bio_revenue']
                tot_r_lit += r['ro_liters']
                tot_r_gal += r['ro_gallons']
                tot_r_rev += r['ro_revenue']
                tot_all_lit += r['total_liters']
                tot_all_gal += r['total_gallons']
                tot_all_rev += r['total_revenue']

                ws.append([
                    i,
                    r['record_date'],
                    r['shift_name'],
                    r['user_name'] or '-',
                    r['bio_meter_start'],
                    r['bio_meter_end'],
                    r['bio_liters'],
                    r['bio_gallons'],
                    r['bio_revenue'],
                    r['ro_meter_start'],
                    r['ro_meter_end'],
                    r['ro_liters'],
                    r['ro_gallons'],
                    r['ro_revenue'],
                    r['total_liters'],
                    r['total_gallons'],
                    r['total_revenue'],
                    r['notes'] or '-'
                ])

                curr_row = ws.max_row
                for col in range(1, 19):
                    c = ws.cell(row=curr_row, column=col)
                    c.border = thin_border
                    c.font = Font(name="Segoe UI", size=10)
                    if col in [1, 2, 3]:
                        c.alignment = Alignment(horizontal='center')
                    elif col in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]:
                        c.alignment = Alignment(horizontal='right')
                        if col in [9, 14, 17]:
                            c.number_format = '#,##0'
                        else:
                            c.number_format = '#,##0.0'

            # Row TOTAL
            ws.append([])
            ws.append([
                "", "TOTAL", "", "",
                "", "", tot_b_lit, tot_b_gal, tot_b_rev,
                "", "", tot_r_lit, tot_r_gal, tot_r_rev,
                tot_all_lit, tot_all_gal, tot_all_rev, ""
            ])
            tot_row_idx = ws.max_row
            tot_fill = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid")
            for col in range(1, 19):
                c = ws.cell(row=tot_row_idx, column=col)
                c.font = Font(name="Segoe UI", size=11, bold=True)
                c.fill = tot_fill
                c.border = thin_border
                if col in [9, 14, 17]:
                    c.number_format = '#,##0'
                elif col in [7, 8, 12, 13, 15, 16]:
                    c.number_format = '#,##0.0'

            # Auto fit column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

            wb.save(file_path)
            messagebox.showinfo("Berhasil", f"Catatan flow meter berhasil diunduh ke:\n{file_path}", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengekspor file Excel:\n{e}", parent=self)
