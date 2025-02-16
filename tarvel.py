import os
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import concurrent.futures
from datetime import datetime, timedelta
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from CTkMessagebox import CTkMessagebox
import json
from pyvis.network import Network
import webbrowser

@dataclass
class MatchResult:
    person_a: str
    person_b: str
    date: str
    time: str
    time_diff: int
    border: str

class ModernTravelAnalyzer:
    def __init__(self):
        # Kaydedilmiş temayı yükle
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                saved_theme = settings.get('theme', 'Dark')
        except:
            saved_theme = 'Dark'  # Varsayılan tema
        
        # Tema ayarı
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")
        
        # Frame renkleri için özel renkler
        self.colors = {
            "bg": "#1a1a2e",          # Ana arka plan
            "frame_bg": "#16213e",    # Frame arka planı
            "button_bg": "#0f3460",   # Buton arka planı
            "hover": "#533483",       # Hover rengi
            "text_box": "#1f2937",    # Metin kutusu arka planı
            "header": "#0d1b2a",      # Başlık arka planı
            "selected": "#1e3a8a",    # Seçili öğe rengi
            "section_bg": "#1e3a8a",  # Bölüm arka planı
            "dark_bg": "#0f172a"      # En koyu arka plan
        }
        
        # Ana pencere ayarları
        self.root = ctk.CTk()
        self.root.title("TAGS Matching v3.0")
        self.root.geometry("1400x900")
        
        # Ana container arka plan rengi
        self.root.configure(fg_color=self.colors["bg"])
        self.main_container = ctk.CTkFrame(
            self.root, 
            fg_color=self.colors["bg"]
        )
        
        # Veri değişkenleri
        self.main_file: Optional[str] = None
        self.comparison_files: List[str] = []
        self.match_results: Dict[str, List[MatchResult]] = {
            'entry': [], 'exit': [], 'complete': []
        }
        
        # Maksimum zaman farkı
        self.max_time = 30
        
        # Arayüz kurulumu
        self.setup_gui()
        
        # Klavye kısayolları
        self.create_keyboard_shortcuts()
        
        # Tema yükleme
        self.load_theme()
        
    def setup_gui(self):
        """Müasir interfeys qurulumu"""
        # Ana konteyner
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Önce durum çubuğunu oluştur
        self.create_status_bar()
        
        # Header toolbar'ı
        self.create_header_tools(self.main_container)
        
        # Sol panel
        self.setup_left_panel()
        
        # Sağ panel
        self.setup_right_panel()
        
    def create_header_tools(self, parent):
        """Yuxarı alət paneli"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        # Logo və başlıq
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="TAGS",
            font=("Helvetica Bold", 32),
            text_color=("#1a73e8", "#64B5F6")
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            title_frame,
            text="Matching v3.0",
            font=("Helvetica", 32),
            text_color=("gray60", "gray70")
        ).pack(side="left")
        
        # Müəllif məlumatları
        author_frame = ctk.CTkFrame(header, fg_color="transparent")
        author_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            author_frame,
            text="by Shahin Hasanov",
            font=("Helvetica", 12, "italic"),
            text_color=("gray60", "gray70")
        ).pack(side="left")
        
        # Toolbar
        tools_frame = ctk.CTkFrame(header, fg_color="transparent")
        tools_frame.pack(side="right")
        
        tools = [
            ("🔄", "Yenilə", self.refresh_data),
            ("📊", "Qrafiklər", self.show_charts),
            ("🕸️", "Şəbəkə", self.show_network_graph),
            ("⚙️", "Parametrlər", self.show_settings),
            ("❓", "Haqqında", self.show_about)
        ]
        
        for icon, tooltip, command in tools:
            btn = ctk.CTkButton(
                tools_frame,
                text=icon,
                width=40,
                height=40,
                command=command,
                corner_radius=10
            )
            btn.pack(side="left", padx=2)
            self.create_tooltip(btn, tooltip)
            
    def setup_left_panel(self):
        """Sol panel qurulumu"""
        left_panel = ctk.CTkFrame(
            self.main_container,
            width=300,
            corner_radius=15,
            fg_color=self.colors["frame_bg"]
        )
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        # Ana dosya seçimi
        self.create_main_file_section(left_panel)
        
        # Karşılaştırma dosyaları
        self.create_comparison_files_section(left_panel)
        
        # İstatistikler
        self.create_statistics_section(left_panel)
        
    def create_main_file_section(self, parent):
        """Əsas fayl seçimi bölməsi"""
        section = ctk.CTkFrame(parent, corner_radius=10)
        section.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(
            section,
            text="Əsas Fayl",
            font=("Helvetica Bold", 14)
        )
        title.pack(pady=10)
        
        self.main_file_btn = ctk.CTkButton(
            section,
            text="Fayl Seç (Ctrl+O)",
            command=self.select_main_file,
            height=40,
            corner_radius=8,
            fg_color=self.colors["button_bg"],
            hover_color=self.colors["hover"]
        )
        self.main_file_btn.pack(pady=10, padx=20, fill="x")
        
        self.main_file_label = ctk.CTkLabel(
            section,
            text="Fayl seçilmədi",
            font=("Helvetica", 12)
        )
        self.main_file_label.pack(pady=5)
        
    def create_comparison_files_section(self, parent):
        """Müqayisə faylları bölməsi"""
        section = ctk.CTkFrame(parent, corner_radius=10, fg_color=self.colors["section_bg"])
        section.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(
            section,
            text="Müqayisə Faylları",
            font=("Helvetica Bold", 14)
        )
        title.pack(pady=10)
        
        # Dosya listesi
        self.files_list = ctk.CTkTextbox(
            section,
            height=150,
            font=("Helvetica", 12),
            fg_color=self.colors["dark_bg"]
        )
        self.files_list.pack(fill="x", padx=10, pady=5)
        
        # Butonlar
        self.comparison_buttons_frame = ctk.CTkFrame(
            section,
            fg_color="transparent"
        )
        self.comparison_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.add_file_btn = ctk.CTkButton(
            self.comparison_buttons_frame,
            text="Fayl Əlavə Et (Ctrl+A)",
            command=self.select_comparison_files,
            state="disabled",
            height=40,
            corner_radius=8,
            fg_color=self.colors["button_bg"],
            hover_color=self.colors["hover"]
        )
        self.add_file_btn.pack(fill="x", pady=(0, 5))
        
        self.clear_btn = ctk.CTkButton(
            self.comparison_buttons_frame,
            text="Təmizlə",
            command=self.clear_comparison_files,
            fg_color="gray30",
            hover_color="gray40",
            state="disabled",
            height=40,
            corner_radius=8
        )
        self.clear_btn.pack(fill="x")
        
    def create_statistics_section(self, parent):
        """Statistika bölməsi"""
        section = ctk.CTkFrame(parent, corner_radius=10)
        section.pack(fill="x", pady=10, padx=10)
        
        title = ctk.CTkLabel(
            section,
            text="Statistika",
            font=("Helvetica Bold", 14)
        )
        title.pack(pady=10)
        
        self.stats_labels = {}
        stats = [
            ("entry", "Giriş Uyğunluqları"),
            ("exit", "Çıxış Uyğunluqları"),
            ("complete", "Tam Uyğunluqlar")
        ]
        
        for key, text in stats:
            frame = ctk.CTkFrame(section, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(
                frame,
                text=text,
                font=("Helvetica", 12)
            ).pack(side="left")
            
            self.stats_labels[key] = ctk.CTkLabel(
                frame,
                text="0",
                font=("Helvetica Bold", 12)
            )
            self.stats_labels[key].pack(side="right")
            
    def setup_right_panel(self):
        """Sağ panel qurulumu"""
        right_panel = ctk.CTkFrame(
            self.main_container,
            corner_radius=15,
            fg_color=self.colors["frame_bg"]
        )
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Arama çubuğu
        self.create_search_frame(right_panel)
        
        # Sonuç tablosu
        self.create_results_table(right_panel)
        
    def create_search_frame(self, parent):
        """Axtarış çərçivəsi"""
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", pady=10)
        
        # Axtarış etiketi
        ctk.CTkLabel(
            search_frame,
            text="Axtarış:",
            font=("Helvetica", 12)
        ).pack(side="left", padx=5)
        
        # Axtarış sahəsi
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        
        # Python 3.13 için trace metodunu güncelle
        self.search_var.trace_add("write", self.on_search_change)

    def create_results_table(self, parent):
        """Nəticələr cədvəli"""
        # Tab butonları
        self.tabs_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.tabs_frame.pack(fill="x", pady=10, padx=10)
        
        self.tab_buttons = {}
        tabs = [
            ("Giriş", "entry", "#1a73e8"),
            ("Çıxış", "exit", "#34a853"),
            ("Tam", "complete", "#673ab7")
        ]
        
        for text, key, color in tabs:
            self.tab_buttons[key] = ctk.CTkButton(
                self.tabs_frame,
                text=text,
                fg_color=color,
                width=120,
                height=35,
                corner_radius=8,
                command=lambda k=key: self.show_tab(k)
            )
            self.tab_buttons[key].pack(side="left", padx=5)
        
        # Sonuç frameleri
        self.result_frames = {}
        for key in ['entry', 'exit', 'complete']:
            frame = ctk.CTkScrollableFrame(
                parent,
                fg_color=self.colors["frame_bg"],
                corner_radius=10
            )
            self.result_frames[key] = frame
            
        # İlk tabı göster
        self.show_tab('entry')
        
    def create_status_bar(self):
        """Status paneli"""
        self.status_bar = ctk.CTkFrame(
            self.root,
            height=30,
            corner_radius=0
        )
        self.status_bar.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Hazırdır",
            font=("Helvetica", 12)
        )
        self.status_label.pack(side="left", padx=10)
        
        self.time_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Helvetica", 12)
        )
        self.time_label.pack(side="right", padx=10)
        
        # Zamanı güncelle
        self.update_time()
        
    def update_time(self):
        """Vaxt etiketini yenilə"""
        self.time_label.configure(
            text=datetime.now().strftime("%H:%M:%S")
        )
        self.root.after(1000, self.update_time)
        
    def create_keyboard_shortcuts(self):
        """Klaviatura qısayolları"""
        self.root.bind("<Control-o>", lambda e: self.select_main_file())
        self.root.bind("<Control-a>", lambda e: self.select_comparison_files())
        self.root.bind("<Control-e>", lambda e: self.export_results())
        self.root.bind("<Control-r>", lambda e: self.refresh_data())
        self.root.bind("<Control-f>", lambda e: self.focus_search())
        self.root.bind("<Escape>", lambda e: self.clear_search())
        
    def show_help(self):
        """Yardım pəncərəsi"""
        help_text = """
        Klaviatura Qısayolları:
        Ctrl+O: Əsas fayl seç
        Ctrl+A: Müqayisə faylı əlavə et
        Ctrl+E: Excel-ə ixrac et
        Ctrl+R: Yenilə
        Ctrl+F: Axtarışa fokuslan
        Esc: Axtarışı təmizlə
        
        Sürüklə-Burax:
        Faylları pəncərəyə sürükləyərək yükləyə bilərsiniz.
        """
        
        CTkMessagebox(
            title="Yardım",
            message=help_text,
            icon="info"
        )
        
    def show_charts(self):
        """Statistika qrafikləri pəncərəsi"""
        if not any(self.match_results.values()):
            CTkMessagebox(
                title="Xəbərdarlıq",
                message="Göstəriləcək məlumat tapılmadı!",
                icon="warning"
            )
            return
            
        chart_window = ctk.CTkToplevel(self.root)
        chart_window.title("İstatistik Grafikleri")
        chart_window.geometry("800x600")
        
        # Tab view oluştur
        tabs = ctk.CTkTabview(chart_window)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekmeleri ekle
        tabs.add("Uyğunluq Paylanması")  # Eşleşme Dağılımı
        tabs.add("Sərhəd Məntəqələri")   # Sınır Noktaları
        tabs.add("Vaxt Təhlili")         # Zaman Analizi
        
        # Grafikleri oluştur
        self.create_match_distribution(tabs.tab("Uyğunluq Paylanması"))
        self.create_border_analysis(tabs.tab("Sərhəd Məntəqələri"))
        self.create_time_analysis(tabs.tab("Vaxt Təhlili"))

    def create_match_distribution(self, parent):
        """Uyğunluq paylanması qrafiki"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Veriyi hazırla
        data = {
            'Giriş': len(self.match_results['entry']),
            'Çıxış': len(self.match_results['exit']),
            'Tam': len(self.match_results['complete'])
        }
        
        # Pasta grafiği için canvas
        canvas = self.create_pie_chart(frame, data)
        canvas.pack(fill="both", expand=True)
        
        # Açıklama
        legend_frame = ctk.CTkFrame(frame, fg_color="transparent")
        legend_frame.pack(fill="x", pady=10)
        
        colors = ['#1a73e8', '#34a853', '#673ab7']
        for (key, value), color in zip(data.items(), colors):
            item_frame = ctk.CTkFrame(legend_frame, fg_color="transparent")
            item_frame.pack(side="left", expand=True)
            
            color_box = ctk.CTkFrame(
                item_frame,
                width=20,
                height=20,
                fg_color=color
            )
            color_box.pack(side="left", padx=5)
            
            ctk.CTkLabel(
                item_frame,
                text=f"{key}: {value}",
                font=("Helvetica", 12)
            ).pack(side="left")

    def create_border_analysis(self, parent):
        """Sərhəd məntəqələri təhlili qrafiki"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sınır noktalarını topla
        border_counts = {}
        for matches in self.match_results.values():
            for match in matches:
                border_counts[match.border] = border_counts.get(match.border, 0) + 1
        
        # Bar grafiği için canvas
        canvas = self.create_bar_chart(
            frame,
            border_counts,
            "Sərhəd Məntəqələrinə Görə Uyğunluqlar"
        )
        canvas.pack(fill="both", expand=True)

    def create_time_analysis(self, parent):
        """Vaxt təhlili qrafiki"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Zaman aralıklarını analiz et
        time_ranges = {
            '0-5 dəq': 0,
            '6-10 dəq': 0,
            '11-15 dəq': 0,
            '16-20 dəq': 0,
            '21-25 dəq': 0,
            '26-30 dəq': 0
        }
        
        for matches in self.match_results.values():
            for match in matches:
                if isinstance(match.time_diff, int):
                    time_diff = match.time_diff
                else:
                    time_diff = int(match.time_diff.split('/')[0])
                
                if time_diff <= 5:
                    time_ranges['0-5 dəq'] += 1
                elif time_diff <= 10:
                    time_ranges['6-10 dəq'] += 1
                elif time_diff <= 15:
                    time_ranges['11-15 dəq'] += 1
                elif time_diff <= 20:
                    time_ranges['16-20 dəq'] += 1
                elif time_diff <= 25:
                    time_ranges['21-25 dəq'] += 1
                else:
                    time_ranges['26-30 dəq'] += 1
        
        # Line grafiği için canvas
        canvas = self.create_line_chart(
            frame,
            time_ranges,
            "Vaxt Aralıqlarına Görə Uyğunluqlar"
        )
        canvas.pack(fill="both", expand=True)

    def create_pie_chart(self, parent, data):
        """Dairə qrafiki yarat"""
        figure = Figure(figsize=(6, 4), dpi=100)
        ax = figure.add_subplot(111)
        
        colors = ['#1a73e8', '#34a853', '#673ab7']
        wedges, texts, autotexts = ax.pie(
            data.values(),
            labels=data.keys(),
            colors=colors,
            autopct='%1.1f%%',
            startangle=90
        )
        
        # Metin renklerini ayarla
        for autotext in autotexts:
            autotext.set_color('white')
        
        canvas = FigureCanvasTkAgg(figure, parent)
        return canvas.get_tk_widget()

    def create_bar_chart(self, parent, data, title):
        """Sütun qrafiki yarat"""
        figure = Figure(figsize=(8, 4), dpi=100)
        ax = figure.add_subplot(111)
        
        x = range(len(data))
        ax.bar(x, data.values(), color='#1a73e8')
        
        # X ekseni etiketleri
        ax.set_xticks(x)
        ax.set_xticklabels(data.keys(), rotation=45, ha='right')
        
        # Başlık ve etiketler
        ax.set_title(title)
        ax.set_ylabel('Uyğunluq Sayı')
        
        # Layout ayarla
        figure.tight_layout()
        
        canvas = FigureCanvasTkAgg(figure, parent)
        return canvas.get_tk_widget()

    def create_line_chart(self, parent, data, title):
        """Xətt qrafiki yarat"""
        figure = Figure(figsize=(8, 4), dpi=100)
        ax = figure.add_subplot(111)
        
        x = range(len(data))
        ax.plot(x, data.values(), 'o-', color='#1a73e8', linewidth=2)
        
        # X ekseni etiketleri
        ax.set_xticks(x)
        ax.set_xticklabels(data.keys(), rotation=45, ha='right')
        
        # Izgara çizgileri
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Başlık ve etiketler
        ax.set_title(title)
        ax.set_ylabel('Uyğunluq Sayı')
        
        # Layout ayarla
        figure.tight_layout()
        
        canvas = FigureCanvasTkAgg(figure, parent)
        return canvas.get_tk_widget()

    def show_settings(self):
        """Parametrlər pəncərəsi"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Parametrlər")
        settings_window.geometry("400x500")
        
        # Ana çerçeve
        main_frame = ctk.CTkFrame(settings_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(
            main_frame,
            text="Ayarlar",
            font=("Helvetica Bold", 20)
        ).pack(pady=10)
        
        # Zaman ayarları
        self.create_time_settings(main_frame)
        
        # Tema ayarları
        self.create_theme_settings(main_frame)
        
        # Tablo ayarları
        self.create_table_settings(main_frame)
        
        # Kaydet butonu
        ctk.CTkButton(
            main_frame,
            text="Saxla",
            command=lambda: self.save_settings(settings_window),
            height=40
        ).pack(pady=20, fill="x")

    def create_time_settings(self, parent):
        """Zaman ayarları bölümü"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Vaxt Parametrləri",
            font=("Helvetica Bold", 14)
        ).pack(pady=10)
        
        # Maksimum zaman farkı
        time_frame = ctk.CTkFrame(frame, fg_color="transparent")
        time_frame.pack(fill="x", padx=10)
        
        ctk.CTkLabel(
            time_frame,
            text="Maksimum Vaxt Fərqi:"
        ).pack(side="left")
        
        self.max_time_var = ctk.StringVar(value="30")
        time_entry = ctk.CTkEntry(
            time_frame,
            textvariable=self.max_time_var,
            width=60
        )
        time_entry.pack(side="right", padx=10)

    def create_theme_settings(self, parent):
        """Temanı dəyişdir"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Tema Parametrləri",
            font=("Helvetica Bold", 14)
        ).pack(pady=10)
        
        # Tema seçimi
        themes = {
            "Sistem": "System",
            "İşıqlı": "Light",
            "Qaranlıq": "Dark"
        }
        
        self.theme_var = ctk.StringVar(value="Qaranlıq")  # Varsayılan değer
        
        for az_name, eng_name in themes.items():
            ctk.CTkRadioButton(
                frame,
                text=az_name,
                variable=self.theme_var,
                value=eng_name,
                command=self.change_theme
            ).pack(pady=5)

    def change_theme(self):
        """Temanı dəyişdir"""
        selected_theme = self.theme_var.get()
        ctk.set_appearance_mode(selected_theme)
        
        # Tema değişikliğini kaydet
        try:
            with open('settings.json', 'w') as f:
                json.dump({'theme': selected_theme}, f)
        except Exception as e:
            print(f"Tema saxlama xətası: {str(e)}")

    def create_table_settings(self, parent):
        """Tablo ayarları bölümü"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            frame,
            text="Cədvəl Parametrləri",
            font=("Helvetica Bold", 14)
        ).pack(pady=10)
        
        # Gösterilecek sütunlar
        columns = [
            "Şəxs Bilgileri",
            "Tarix",
            "Saat",
            "Vaxt Fərqi",
            "Sərhəd Məntəqəsi"
        ]
        
        self.column_vars = {}
        for col in columns:
            var = ctk.BooleanVar(value=True)
            self.column_vars[col] = var
            
            ctk.CTkCheckBox(
                frame,
                text=col,
                variable=var
            ).pack(pady=2)

    def save_settings(self, window):
        """Parametrləri saxla"""
        try:
            max_time = int(self.max_time_var.get())
            if 5 <= max_time <= 60:
                self.max_time = max_time
            else:
                raise ValueError
        except ValueError:
            CTkMessagebox(
                title="Xəta",
                message="Maksimum zaman 5-60 dakika arasında olmalıdır!",
                icon="error"
            )
            return
        
        # Tema ayarı
        ctk.set_appearance_mode(self.theme_var.get())
        
        # Tablo ayarları
        self.update_columns()
        
        # Pencereyi kapat
        window.destroy()
        
        CTkMessagebox(
            title="Uğurlu",
            message="Parametrlər saxlanıldı!",
            icon="check"
        )

    def update_columns(self):
        """Cədvəl sütunlarını yenilə"""
        # Görünür sütunları güncelle
        visible_columns = [
            col for col, var in self.column_vars.items()
            if var.get()
        ]
        
        # Tüm sonuç framelerini güncelle
        for frame in self.result_frames.values():
            self.refresh_results_table(frame, visible_columns)

    def create_tooltip(self, widget, text):
        """İpucu yarat"""
        tooltip = ctk.CTkFrame(self.root)
        label = ctk.CTkLabel(
            tooltip,
            text=text,
            font=("Helvetica", 11)
        )
        label.pack(padx=5, pady=2)
        
        def enter(e):
            tooltip.place(
                x=widget.winfo_rootx() + widget.winfo_width(),
                y=widget.winfo_rooty()
            )
        
        def leave(e):
            tooltip.place_forget()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def run(self):
        """Tətbiqi başlat"""
        self.root.mainloop()

    def refresh_data(self):
        """Məlumatları yenilə"""
        try:
            # Sonuçları temizle
            self.match_results = {
                'entry': [], 
                'exit': [], 
                'complete': []
            }
            
            # Tüm frameleri temizle
            for frame in self.result_frames.values():
                for widget in frame.winfo_children():
                    widget.destroy()
            
            # İstatistikleri sıfırla
            for label in self.stats_labels.values():
                label.configure(text="0")
            
            # Durum çubuğunu güncelle
            self.status_label.configure(text="Yenilənir...")
            
            # Eğer dosyalar varsa analizi tekrar başlat
            if self.main_file and self.comparison_files:
                self.analyze_data()
                self.status_label.configure(text="Analiz tamamlandı")
            else:
                self.status_label.configure(text="Hazırdır")
            
        except Exception as e:
            self.status_label.configure(text="Yenilənmə hatası!")
            messagebox.showerror("Hata", f"Yenilənmə hatası: {str(e)}")

    def select_main_file(self):
        """Ana dosya seçimi"""
        try:
            file_path = filedialog.askopenfilename(
                title="Əsas faylı seçin",
                filetypes=[("Excel faylları", "*.xlsx;*.xls")],
                initialdir=os.path.expanduser("~")  # Kullanıcı klasöründen başla
            )
            
            if file_path:
                self.main_file = file_path
                self.main_file_label.configure(
                    text=os.path.basename(file_path)
                )
                self.add_file_btn.configure(state="normal")
                self.status_label.configure(
                    text="Əsas fayl yükləndi"
                )
                
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Fayl seçimi xətası: {str(e)}",
                icon="error"
            )

    def select_comparison_files(self):
        """Müqayisə fayllarını seç"""
        try:
            filenames = filedialog.askopenfilenames(
                title="Karşılaştırma Dosyalarını Seç",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if filenames:
                # Her seçilen dosya için
                for filename in filenames:
                    try:
                        # Dosyayı oku ve kontrol et
                        df = pd.read_excel(filename)
                        required_columns = [
                            'Keçid zamanı', 
                            'Soyadı, Adı (Lat)', 
                            'İstiqamət', 
                            'Sərhəd nəzarət məntəqəsi'
                        ]
                        
                        if all(col in df.columns for col in required_columns):
                            # Tekrarı önle
                            if filename not in self.comparison_files:
                                self.comparison_files.append(filename)
                                
                                # Dosya listesini güncelle
                                self.files_list.delete("1.0", "end")
                                for idx, file in enumerate(self.comparison_files, 1):
                                    self.files_list.insert("end", f"{idx}. {os.path.basename(file)}\n")
                                
                                # Temizle butonunu aktif et
                                self.clear_btn.configure(state="normal")
                                
                                # Durum çubuğunu güncelle
                                self.status_label.configure(text="Müqayisə faylı əlavə edildi")
                                
                        else:
                            missing_cols = [col for col in required_columns if col not in df.columns]
                            CTkMessagebox(
                                title="Xəta",
                                message=f"{os.path.basename(filename)}: Gerekli sütunlar eksik: {', '.join(missing_cols)}",
                                icon="error"
                            )
                            
                    except Exception as e:
                        CTkMessagebox(
                            title="Xəta",
                            message=f"{os.path.basename(filename)}: Fayl oxuma xətası: {str(e)}",
                            icon="error"
                        )
                
                # Dosyalar eklendiyse analizi başlat
                if self.comparison_files:
                    self.analyze_data()
                
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Fayl seçmə hatası: {str(e)}",
                icon="error"
            )

    def clear_comparison_files(self):
        """Müqayisə fayllarını təmizlə"""
        try:
            # Dosya listesini temizle
            self.comparison_files = []
            
            # Metin kutusunu temizle
            self.files_list.delete("1.0", "end")
            
            # Butonları devre dışı bırak
            self.clear_btn.configure(state="disabled")
            
            # Sonuçları temizle
            self.match_results = {
                'entry': [], 
                'exit': [], 
                'complete': []
            }
            
            # Tüm frameleri temizle
            for frame in self.result_frames.values():
                for widget in frame.winfo_children():
                    widget.destroy()
            
            # İstatistikleri sıfırla
            for label in self.stats_labels.values():
                label.configure(text="0")
            
            # Durum çubuğunu güncelle
            self.status_label.configure(text="Müqayisə faylları təmizləndi")
            
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Temizlənmə hatası: {str(e)}",
                icon="error"
            )

    def on_search_change(self, *args):
        """Arama değiştiğinde çağrılır"""
        try:
            search_text = self.search_var.get().lower()
            
            # Aktif tab'ı bul
            active_tab = None
            for key, frame in self.result_frames.items():
                if str(frame.winfo_manager()) != "":
                    active_tab = key
                    break
            
            if active_tab:
                # Tüm sonuçları gizle
                for widget in self.result_frames[active_tab].winfo_children():
                    widget.pack_forget()
                
                # Arama kriterlerine uyan sonuçları göster
                for match in self.match_results[active_tab]:
                    if (search_text in match.person_a.lower() or 
                        search_text in match.person_b.lower() or 
                        search_text in match.border.lower() or 
                        search_text in match.date.lower()):
                        
                        # Sonuç satırını yeniden oluştur
                        self.create_result_row(
                            self.result_frames[active_tab],
                            match,
                            self.match_results[active_tab],
                            active_tab
                        )
                
                # Durum çubuğunu güncelle
                visible_count = len(self.result_frames[active_tab].winfo_children())
                total_count = len(self.match_results[active_tab])
                self.status_label.configure(
                    text=f"Göstərilən: {visible_count}/{total_count}"
                )
                
        except Exception as e:
            self.status_label.configure(text=f"Arama hatası: {str(e)}")

    def show_tab(self, tab_name: str):
        """Tab değiştirme"""
        try:
            # Tüm tabları gizle
            for frame in self.result_frames.values():
                frame.pack_forget()
            
            # Seçilen tabı göster
            self.result_frames[tab_name].pack(fill="both", expand=True, padx=10, pady=10)
            
            # Tab butonlarını güncelle
            for key, button in self.tab_buttons.items():
                if key == tab_name:
                    button.configure(fg_color=self.get_tab_color(key))
                else:
                    button.configure(fg_color="transparent")
            
            # Durum çubuğunu güncelle
            count = len(self.match_results[tab_name])
            self.status_label.configure(text=f"{tab_name.title()} uyğunluqları: {count}")
            
        except Exception as e:
            self.status_label.configure(text=f"Tab değiştirme hatası: {str(e)}")

    def get_tab_color(self, tab_name: str) -> str:
        """Tab rengini döndür"""
        colors = {
            'entry': '#1a73e8',    # Mavi
            'exit': '#34a853',     # Yeşil
            'complete': '#673ab7'   # Mor
        }
        return colors.get(tab_name, 'transparent')

    def analyze_data(self):
        """Verileri analiz et ve sonuçları sırala"""
        try:
            if not self.main_file or not self.comparison_files:
                print("Dosyalar eksik")  # Debug
                return
            
            # Ana dosyayı oku
            main_df = pd.read_excel(self.main_file)
            print(f"Ana dosya okundu: {len(main_df)} satır")  # Debug
            
            # Sonuçları temizle
            self.match_results = {
                'entry': [],
                'exit': [],
                'complete': []
            }
            
            # Her karşılaştırma dosyası için
            for comp_file in self.comparison_files:
                try:
                    # Karşılaştırma dosyasını oku
                    comp_df = pd.read_excel(comp_file)
                    print(f"Karşılaştırma dosyası okundu: {len(comp_df)} satır")  # Debug
                    
                    # Giriş ve çıkış eşleşmelerini bul
                    entry_matches = self.find_matches(main_df, comp_df, 'Giriş')
                    exit_matches = self.find_matches(main_df, comp_df, 'Çıxış')
                    
                    print(f"Bulunan eşleşmeler - Giriş: {len(entry_matches)}, Çıkış: {len(exit_matches)}")  # Debug
                    
                    # Sonuçları listeye ekle
                    self.match_results['entry'].extend(entry_matches)
                    self.match_results['exit'].extend(exit_matches)
                    
                    # Tam eşleşmeleri bul
                    complete_matches = self.find_complete_matches(entry_matches, exit_matches)
                    print(f"Tam eşleşmeler: {len(complete_matches)}")  # Debug
                    
                    self.match_results['complete'].extend(complete_matches)
                    
                except Exception as e:
                    print(f"Dosya analiz hatası: {str(e)}")  # Debug
                    CTkMessagebox(
                        title="Xəbərdarlıq",
                        message=f"{os.path.basename(comp_file)} dosyası analiz edilirken hata: {str(e)}",
                        icon="warning"
                    )
            
            print(f"Toplam sonuçlar: {self.match_results}")  # Debug
            
            # Sonuçları göster
            self.display_results()
            
            # İstatistikleri güncelle
            self.update_statistics()
            
            # Durum çubuğunu güncelle
            total_matches = sum(len(matches) for matches in self.match_results.values())
            self.status_label.configure(text=f"Analiz tamamlandı. Cəmi {total_matches} uyğunluq tapıldı")
            
        except Exception as e:
            print(f"Analiz ana hata: {str(e)}")  # Debug
            CTkMessagebox(
                title="Xəta",
                message=f"Analiz hatası: {str(e)}",
                icon="error"
            )

    def find_matches(self, df1: pd.DataFrame, df2: pd.DataFrame, direction: str) -> List[MatchResult]:
        """Giriş və ya çıxış uyğunluqlarını tap"""
        try:
            # İstiqamətə görə filtrele
            df1_filtered = df1[df1['İstiqamət'] == direction].copy()
            df2_filtered = df2[df2['İstiqamət'] == direction].copy()
            
            # Tarihleri datetime'a çevir
            df1_filtered['datetime'] = pd.to_datetime(df1_filtered['Keçid zamanı'], format='%d.%m.%Y %H:%M')
            df2_filtered['datetime'] = pd.to_datetime(df2_filtered['Keçid zamanı'], format='%d.%m.%Y %H:%M')
            
            matches = []
            for _, row1 in df1_filtered.iterrows():
                for _, row2 in df2_filtered.iterrows():
                    # Farklı kişiler olmalı
                    if row1['Soyadı, Adı (Lat)'] != row2['Soyadı, Adı (Lat)']:
                        # Zaman farkını hesapla
                        time_diff = abs((row1['datetime'] - row2['datetime']).total_seconds() / 60)
                        
                        # 30 dakikadan az fark varsa
                        if time_diff <= self.max_time:
                            matches.append(MatchResult(
                                person_a=row1['Soyadı, Adı (Lat)'],
                                person_b=row2['Soyadı, Adı (Lat)'],
                                date=row1['datetime'].strftime('%d.%m.%Y'),
                                time=f"{row1['datetime'].strftime('%H:%M')}-{row2['datetime'].strftime('%H:%M')}",
                                time_diff=int(time_diff),
                                border=row1['Sərhəd nəzarət məntəqəsi']
                            ))
            
            return matches
            
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Eşleşme arama hatası: {str(e)}",
                icon="error"
            )
            return []

    def find_complete_matches(self, entry_matches: List[MatchResult], 
                             exit_matches: List[MatchResult]) -> List[MatchResult]:
        """Tam uyğunluqları tap"""
        complete_matches = []
        seen_pairs = set()
        
        for entry in entry_matches:
            for exit in exit_matches:
                # Aynı kişiler ve sınır noktası kontrolü
                if (entry.person_a == exit.person_a and 
                    entry.person_b == exit.person_b and 
                    entry.border == exit.border):
                    
                    # Tarih kontrolü
                    entry_date = datetime.strptime(f"{entry.date} {entry.time.split('-')[0]}", '%d.%m.%Y %H:%M')
                    exit_date = datetime.strptime(f"{exit.date} {exit.time.split('-')[0]}", '%d.%m.%Y %H:%M')
                    
                    if exit_date > entry_date:
                        pair_key = f"{entry.person_a}_{entry.person_b}_{entry.date}_{exit.date}"
                        
                        if pair_key not in seen_pairs:
                            complete_matches.append(MatchResult(
                                person_a=entry.person_a,
                                person_b=entry.person_b,
                                date=f"{entry.date} - {exit.date}",
                                time=f"{entry.time} - {exit.time}",
                                time_diff=f"{entry.time_diff}/{exit.time_diff}",
                                border=entry.border
                            ))
                            seen_pairs.add(pair_key)
        
        return complete_matches

    def display_results(self):
        """Nəticələri göstər"""
        try:
            # Tüm frameleri temizle
            for frame in self.result_frames.values():
                for widget in frame.winfo_children():
                    widget.destroy()
            
            # Her kategori için başlık satırı oluştur
            headers = [
                ("Şəxs A (Sayı)", 200), 
                ("Şəxs B (Sayı)", 200), 
                ("Tarix", 150),
                ("Saat", 150), 
                ("Vaxt Fərqi", 100), 
                ("Sərhəd Məntəqəsi", 200)
            ]
            
            # Tab renklerini belirle
            tab_colors = {
                'entry': '#1a73e8',  # Mavi
                'exit': '#34a853',   # Yeşil
                'complete': '#673ab7' # Mor
            }
            
            # Her kategori için sonuçları göster ve sırala
            for category in ['entry', 'exit', 'complete']:
                frame = self.result_frames[category]
                
                # Her kategoride kişilerin toplam eşleşme sayısını hesapla
                person_counts = {}
                for match in self.match_results[category]:
                    person_counts[match.person_a] = person_counts.get(match.person_a, 0) + 1
                    person_counts[match.person_b] = person_counts.get(match.person_b, 0) + 1
                
                # Başlık satırı
                header_frame = ctk.CTkFrame(frame, fg_color=tab_colors[category])
                header_frame.pack(fill="x", pady=(0, 10))
                
                # Toplam sayı gösterimi
                total_label = ctk.CTkLabel(
                    header_frame,
                    text=f"Ümumi: {len(self.match_results[category])}",
                    font=("Helvetica Bold", 12)
                )
                total_label.pack(side="right", padx=10, pady=5)
                
                # Header etiketleri
                for text, width in headers:
                    label = ctk.CTkLabel(
                        header_frame,
                        text=text,
                        font=("Helvetica Bold", 12),
                        width=width
                    )
                    label.pack(side="left", padx=5, pady=5)
                
                # Sonuçları eşleşme sayısına ve zaman farkına göre sırala
                sorted_matches = sorted(
                    self.match_results[category],
                    key=lambda x: (
                        -(person_counts[x.person_a] + person_counts[x.person_b]),  # Önce eşleşme sayısına göre azalan
                        float(x.time_diff.split('/')[0]) if isinstance(x.time_diff, str) 
                        else float(x.time_diff)  # Sonra zaman farkına göre artan
                    )
                )
                
                # Sıralanmış sonuçları göster
                for match in sorted_matches:
                    row = ctk.CTkFrame(frame)
                    row.pack(fill="x", pady=2)
                    
                    # Zaman farkına göre renk
                    time_diff = (
                        float(match.time_diff.split('/')[0]) 
                        if isinstance(match.time_diff, str) 
                        else float(match.time_diff)
                    )
                    
                    # Renk belirleme
                    if category == 'complete':
                        bg_color = "#8B0000"  # Tam eşleşmeler için koyu kırmızı
                    else:
                        bg_color = self.get_time_diff_color(time_diff)
                    
                    row.configure(fg_color=bg_color)
                    
                    # Veri alanları
                    fields = [
                        (f"{match.person_a} ({person_counts[match.person_a]})", 200),
                        (f"{match.person_b} ({person_counts[match.person_b]})", 200),
                        (match.date, 150),
                        (match.time, 150),
                        (f"{match.time_diff} dk", 100),
                        (match.border, 200)
                    ]
                    
                    for text, width in fields:
                        label = ctk.CTkLabel(
                            row,
                            text=str(text),
                            font=("Helvetica", 12),
                            width=width
                        )
                        label.pack(side="left", padx=5, pady=5)
                
                # Sıralanmış sonuçları kaydet
                self.match_results[category] = sorted_matches
            
            # İstatistikleri güncelle
            self.update_statistics()
            
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Nəticələri göstərmə xətası: {str(e)}",
                icon="error"
            )

    def create_result_row(self, parent, match, person_counts, category):
        """Nəticə sətri yarat"""
        try:
            # Satır container'ı
            row = ctk.CTkFrame(parent)
            row.pack(fill="x", pady=2)
            
            # Arkaplan rengini belirle
            if category == 'complete':
                bg_color = "#8B0000"  # Tam eşleşmeler için koyu kırmızı
            else:
                # Zaman farkına göre renk
                time_diff = (
                    float(match.time_diff.split('/')[0]) 
                    if isinstance(match.time_diff, str) 
                    else float(match.time_diff)
                )
                bg_color = self.get_time_diff_color(time_diff)
            
            row.configure(fg_color=bg_color)
            
            # Veri alanları
            fields = [
                (f"{match.person_a} ({person_counts[match.person_a]})", 200),
                (f"{match.person_b} ({person_counts[match.person_b]})", 200),
                (match.date, 150),
                (match.time, 150),
                (f"{match.time_diff} dk", 100),
                (match.border, 200)
            ]
            
            for text, width in fields:
                label = ctk.CTkLabel(
                    row,
                    text=str(text),
                    font=("Helvetica", 12),
                    width=width
                )
                label.pack(side="left", padx=5, pady=5)
            
        except Exception as e:
            print(f"Sətir yaratma xətası: {str(e)}")

    def get_time_diff_color(self, time_diff: int) -> str:
        """Vaxt fərqinə görə rəng qaytar"""
        if time_diff <= 15:
            return "#1b5e20"  # Koyu yeşil
        elif time_diff <= 30:
            return "#f9a825"  # Sarı
        return "#c62828"  # Kırmızı

    def update_statistics(self):
        """Statistikanı yenilə"""
        try:
            for category in ['entry', 'exit', 'complete']:
                count = len(self.match_results[category])
                self.stats_labels[category].configure(
                    text=str(count)
                )
            
        except Exception as e:
            print(f"İstatistik güncelleme hatası: {str(e)}")

    def show_network_graph(self):
        """Şəbəkə vizuallaşdırması"""
        try:
            if not any(self.match_results.values()):
                CTkMessagebox(
                    title="Xəbərdarlıq",
                    message="Göstəriləcək məlumat tapılmadı!",
                    icon="warning"
                )
                return
            
            # Network oluştur
            net = Network(
                height="750px", 
                width="100%", 
                bgcolor="#222222", 
                font_color="white",
                directed=True,
                notebook=False
            )
            
            # Düğümleri ekle
            added_nodes = set()
            for match_type, matches in self.match_results.items():
                for match in matches:
                    if match.person_a not in added_nodes:
                        net.add_node(match.person_a, title=match.person_a)
                        added_nodes.add(match.person_a)
                    if match.person_b not in added_nodes:
                        net.add_node(match.person_b, title=match.person_b)
                        added_nodes.add(match.person_b)
                    
                    # Kenar rengi
                    edge_color = {
                        'entry': '#4CAF50',  # Yeşil
                        'exit': '#F44336',   # Kırmızı
                        'complete': '#9C27B0' # Mor
                    }.get(match_type, '#2196F3')
                    
                    net.add_edge(
                        match.person_a,
                        match.person_b,
                        color=edge_color,
                        title=f"Tarix: {match.date}\nSaat: {match.time}\nSərhəd: {match.border}"
                    )

            # Ağ seçeneklerini ayarla
            net.set_options("""
            {
                "nodes": {
                    "font": {"size": 16},
                    "color": {"border": "#ffffff"},
                    "shadow": {"enabled": true}
                },
                "edges": {
                    "smooth": {"type": "continuous"},
                    "arrows": {"to": {"enabled": true}},
                    "color": {"inherit": false}
                },
                "physics": {
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "centralGravity": 0.3,
                        "springLength": 200
                    },
                    "minVelocity": 0.75
                }
            }
            """)

            # Geçici dosya yolu
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network.html")

            try:
                # Ağı kaydet
                net.save_graph(output_path)
                
                # Tarayıcıda aç
                webbrowser.open(f'file://{output_path}', new=2)
                
            except Exception as e:
                raise Exception(f"HTML işleme hatası: {str(e)}")

        except Exception as e:
            print(f"Network hatası: {str(e)}")
            CTkMessagebox(
                title="Xəta",
                message=f"Şəbəkə xətası: {str(e)}",
                icon="warning"
            )

    def refresh_results_table(self, frame, visible_columns):
        """Nəticələr cədvəlini yenilə"""
        try:
            # Aktif tabı bul
            active_tab = None
            for key, tab_frame in self.result_frames.items():
                if tab_frame == frame:
                    active_tab = key
                    break
                
            if not active_tab:
                return
            
            # Mevcut içeriği temizle
            for widget in frame.winfo_children():
                widget.destroy()
            
            # Başlık satırını güncelle
            header_frame = ctk.CTkFrame(frame, fg_color=self.colors["section_bg"])
            header_frame.pack(fill="x", pady=(0, 10))
            
            # Toplam sayı etiketi
            total_label = ctk.CTkLabel(
                header_frame,
                text=f"Ümumi: {len(self.match_results[active_tab])}",
                font=("Helvetica Bold", 12),
                width=100
            )
            total_label.pack(side="right", padx=10, pady=5)
            
            # Görünür sütunlar için başlıklar
            column_widths = {
                "Şəxs A": 200,
                "Şəxs B": 200,
                "Tarix": 150,
                "Saat": 150,
                "Vaxt Fərqi": 100,
                "Sərhəd Məntəqəsi": 200,
                "Təkrar": 80  # Yeni sütun
            }
            
            for col in visible_columns:
                label = ctk.CTkLabel(
                    header_frame,
                    text=col,
                    font=("Helvetica Bold", 12),
                    width=column_widths.get(col, 150)
                )
                label.pack(side="left", padx=5, pady=5)
            
            # Kişi sayılarını hesapla
            person_counts = {}
            for match in self.match_results[active_tab]:
                person_counts[match.person_a] = person_counts.get(match.person_a, 0) + 1
                person_counts[match.person_b] = person_counts.get(match.person_b, 0) + 1
            
            # Sonuç satırlarını güncelle
            for match in self.match_results[active_tab]:
                row = ctk.CTkFrame(frame)
                row.pack(fill="x", pady=2)
                
                # Zaman farkına göre renk
                time_diff = (
                    int(match.time_diff.split('/')[0]) 
                    if isinstance(match.time_diff, str) 
                    else match.time_diff
                )
                bg_color = self.get_time_diff_color(time_diff)
                row.configure(fg_color=bg_color)
                
                # Görünür sütunlar için veriler
                field_map = {
                    "Şəxs A": (f"{match.person_a} ({person_counts[match.person_a]})", 200),
                    "Şəxs B": (f"{match.person_b} ({person_counts[match.person_b]})", 200),
                    "Tarix": (match.date, 150),
                    "Saat": (match.time, 150),
                    "Vaxt Fərqi": (f"{match.time_diff} dk", 100),
                    "Sərhəd Məntəqəsi": (match.border, 200)
                }
                
                for col in visible_columns:
                    if col in field_map:
                        text, width = field_map[col]
                        label = ctk.CTkLabel(
                            row,
                            text=str(text),
                            font=("Helvetica", 12),
                            width=width
                        )
                        label.pack(side="left", padx=5, pady=5)
                        
        except Exception as e:
            print(f"Cədvəl yeniləmə xətası: {str(e)}")

    def toggle_filter_options(self):
        """Filtr seçimlərini göstər/gizlət"""
        if self.filtr_cercivesi.winfo_manager():
            self.filtr_cercivesi.pack_forget()
            self.filtr_duymesi.configure(text="Filtrlə ▼")
        else:
            self.filtr_cercivesi.pack(fill="x", pady=5)
            self.filtr_duymesi.configure(text="Filtrlə ▲")

    def apply_filters(self):
        """Seçilmiş filtrləri tətbiq et"""
        try:
            # Aktiv tabı tap
            aktiv_tab = None
            for acar, cercive in self.result_frames.items():
                if str(cercive.winfo_manager()) != "":
                    aktiv_tab = acar
                    break
            
            if aktiv_tab:
                # Bütün nəticələri gizle
                for widget in self.result_frames[aktiv_tab].winfo_children():
                    widget.pack_forget()
                
                # Filtrləri al
                vaxt_filtri = self.vaxt_filtri.get()
                serhed_filtri = self.serhed_filtri.get()
                tarix_filtri = self.tarix_filtri.get()
                
                filtrlenmis_neticeler = []
                for netice in self.match_results[aktiv_tab]:
                    # Vaxt filtri
                    vaxt_uygunlugu = True
                    if vaxt_filtri != "Hamısı":
                        vaxt_ferqi = (
                            netice.time_diff if isinstance(netice.time_diff, (int, float))
                            else float(netice.time_diff.split('/')[0])
                        )
                        if vaxt_filtri == "0-5 dəq":
                            vaxt_uygunlugu = 0 <= vaxt_ferqi <= 5
                        elif vaxt_filtri == "5-15 dəq":
                            vaxt_uygunlugu = 5 < vaxt_ferqi <= 15
                        elif vaxt_filtri == "15+ dəq":
                            vaxt_uygunlugu = vaxt_ferqi > 15
                    
                    # Sərhəd məntəqəsi filtri
                    serhed_uygunlugu = serhed_filtri == "Hamısı" or netice.border == serhed_filtri
                    
                    # Tarix filtri
                    tarix_uygunlugu = True
                    if tarix_filtri != "Hamısı":
                        netice_tarixi = datetime.strptime(netice.date.split(' - ')[0], '%d.%m.%Y')
                        bu_gun = datetime.now()
                        if tarix_filtri == "Bu gün":
                            tarix_uygunlugu = netice_tarixi.date() == bu_gun.date()
                        elif tarix_filtri == "Son 3 gün":
                            tarix_uygunlugu = (bu_gun - netice_tarixi).days <= 3
                        elif tarix_filtri == "Son həftə":
                            tarix_uygunlugu = (bu_gun - netice_tarixi).days <= 7
                    
                    # Bütün filtrlərə uyğundursa əlavə et
                    if vaxt_uygunlugu and serhed_uygunlugu and tarix_uygunlugu:
                        filtrlenmis_neticeler.append(netice)
                
                # Nəticələri göstər və sayları hesabla
                sexs_sayi = {}
                for netice in filtrlenmis_neticeler:
                    sexs_sayi[netice.person_a] = sexs_sayi.get(netice.person_a, 0) + 1
                    sexs_sayi[netice.person_b] = sexs_sayi.get(netice.person_b, 0) + 1
                
                # Nəticələri sayına görə sırala
                filtrlenmis_neticeler = sorted(
                    filtrlenmis_neticeler,
                    key=lambda x: (
                        -(sexs_sayi[x.person_a] + sexs_sayi[x.person_b]),  # Sayına görə azalan
                        float(x.time_diff.split('/')[0]) if isinstance(x.time_diff, str) 
                        else float(x.time_diff)  # Sonra vaxta görə artan
                    )
                )
                
                # Sıralanmış nəticələri göstər
                for netice in filtrlenmis_neticeler:
                    self.create_result_row(
                        self.result_frames[aktiv_tab],
                        netice,
                        sexs_sayi,
                        aktiv_tab
                    )
                
                # Status panelini yenilə
                umumi_say = len(self.match_results[aktiv_tab])
                filtrlenmis_say = len(filtrlenmis_neticeler)
                self.status_label.configure(
                    text=f"Göstərilən: {filtrlenmis_say}/{umumi_say}"
                )
        
        except Exception as e:
            CTkMessagebox(
                title="Xəta",
                message=f"Filtr tətbiq xətası: {str(e)}",
                icon="error"
            )

    def reset_filters(self):
        """Filtrləri sıfırla"""
        self.vaxt_filtri.set("Hamısı")
        self.serhed_filtri.set("Hamısı")
        self.tarix_filtri.set("Hamısı")
        self.apply_filters()

    def show_about(self):
        """Haqqında pəncərəsi"""
        about_text = """
        TAGS Matching v3.0
        
        Bu proqram sərhəd keçidlərində şübhəli uyğunluqları 
        aşkar etmək üçün hazırlanmışdır.
        
        Xüsusiyyətlər:
        • Giriş/Çıxış uyğunluqları
        • Tam uyğunluqlar
        • Statistika və qrafiklər
        • Şəbəkə vizuallaşdırması
        • Filtrlər və axtarış
        
        Müəllif: Shahin Hasanov
        © 2024 Bütün hüquqlar qorunur
        """
        
        CTkMessagebox(
            title="Haqqında",
            message=about_text,
            icon="info"
        )

    def load_theme(self):
        """Temanı yüklə"""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                ctk.set_appearance_mode(settings['theme'])
        except Exception as e:
            print(f"Tema yüklənmə xətası: {str(e)}")

if __name__ == "__main__":
    app = ModernTravelAnalyzer()
    app.run()