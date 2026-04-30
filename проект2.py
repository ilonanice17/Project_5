import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
import json
from datetime import datetime

class WeatherEntry:
    def __init__(self, date, temperature, description, precipitation):
        self.date = date
        self.temperature = temperature
        self.description = description
        self.precipitation = precipitation

    def __str__(self):
        precip_str = "Да" if self.precipitation else "Нет"
        return f"{self.date.strftime('%Y-%m-%d')} | {self.temperature:.1f}°C | {self.description} | Осадки: {precip_str}"

    def to_json(self):
        return {
            "date": self.date.isoformat(),
            "temperature": self.temperature,
            "description": self.description,
            "precipitation": self.precipitation
        }

    @staticmethod
    def from_json(data):
        date_obj = datetime.fromisoformat(data["date"])
        return WeatherEntry(date_obj, data["temperature"], data["description"], data["precipitation"])


class WeatherDiaryApp:
    def __init__(self, master):
        self.master = master
        master.title("Дневник погоды")
        master.geometry("850x700")
        master.resizable(False, False)

        self.weather_entries = []
        self.json_filename = "weather_diary.json"

        self.create_widgets()
        self.load_entries_from_json()
        self.update_treeview()

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self.master, text="Запись о погоде", padding="10")
        input_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(input_frame, text="Дата:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = DateEntry(input_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Температура (°C):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.temp_entry = ttk.Entry(input_frame, width=10)
        self.temp_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Описание:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(input_frame, width=40)
        self.desc_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Осадки:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.precip_var = tk.StringVar()
        self.precip_combobox = ttk.Combobox(input_frame, textvariable=self.precip_var, values=["Нет", "Да"], state="readonly", width=5)
        self.precip_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.precip_combobox.set("Нет")

        self.btn_add = ttk.Button(input_frame, text="Добавить запись", command=self.add_entry)
        self.btn_add.grid(row=3, column=0, columnspan=4, pady=10)

        filter_frame = ttk.LabelFrame(self.master, text="Фильтры", padding="10")
        filter_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(filter_frame, text="Дата:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filter_date_entry = DateEntry(filter_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.filter_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(filter_frame, text="Температура >:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.filter_temp_entry = ttk.Entry(filter_frame, width=5)
        self.filter_temp_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        self.btn_apply_filter = ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filters)
        self.btn_apply_filter.grid(row=0, column=4, padx=10)
        self.btn_reset_filter = ttk.Button(filter_frame, text="Сбросить", command=self.reset_filters)
        self.btn_reset_filter.grid(row=0, column=5, padx=5)

        list_frame = ttk.LabelFrame(self.master, text="Записи о погоде", padding="10")
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(list_frame, columns=("Date", "Temperature", "Description", "Precipitation"), show="headings")
        self.tree.heading("Date", text="Дата")
        self.tree.heading("Temperature", text="Температура (°C)")
        self.tree.heading("Description", text="Описание")
        self.tree.heading("Precipitation", text="Осадки")

        self.tree.column("Date", width=100, anchor=tk.CENTER)
        self.tree.column("Temperature", width=100, anchor=tk.CENTER)
        self.tree.column("Description", width=300, anchor=tk.W)
        self.tree.column("Precipitation", width=80, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_entry_select)

        list_buttons_frame = ttk.Frame(self.master, padding="10")
        list_buttons_frame.pack(fill=tk.X)

        self.btn_delete = ttk.Button(list_buttons_frame, text="Удалить выбранную", command=self.delete_selected_entry, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT, padx=5)
        self.btn_clear_all = ttk.Button(list_buttons_frame, text="Очистить все", command=self.clear_all_entries)
        self.btn_clear_all.pack(side=tk.LEFT, padx=5)
        self.btn_save = ttk.Button(list_buttons_frame, text="Сохранить", command=self.save_entries_to_json)
        self.btn_save.pack(side=tk.RIGHT, padx=5)

    def load_entries_from_json(self):
        try:
            with open(self.json_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.weather_entries = [WeatherEntry.from_json(entry) for entry in data]
        except FileNotFoundError:
            self.weather_entries = []
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка загрузки", "Ошибка при чтении файла JSON. Файл может быть поврежден.")
            self.weather_entries = []
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Произошла непредвиденная ошибка при загрузке: {e}")
            self.weather_entries = []

    def save_entries_to_json(self):
        try:
            with open(self.json_filename, 'w', encoding='utf-8') as f:
                json_data = [entry.to_json() for entry in self.weather_entries]
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Успех", "Данные сохранены.")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {e}")

    def validate_entry_data(self):
        try:
            date_str = self.date_entry.get_date().strftime('%Y-%m-%d')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "Некорректный формат даты. Используйте YYYY-MM-DD.")
            return None

        try:
            temp_str = self.temp_entry.get().strip()
            if not temp_str:
                messagebox.showwarning("Ошибка ввода", "Температура не может быть пустой.")
                return None
            temperature = float(temp_str)
        except ValueError:
            messagebox.showwarning("Ошибка ввода", "Температура должна быть числом.")
            return None

        description = self.desc_entry.get().strip()
        if not description:
            messagebox.showwarning("Ошибка ввода", "Описание погоды не может быть пустым.")
            return None

        precipitation_str = self.precip_combobox.get()
        precipitation = True if precipitation_str == "Да" else False

        return date_obj, temperature, description, precipitation

    def add_entry(self):
        validation_result = self.validate_entry_data()
        if validation_result:
            date_obj, temperature, description, precipitation = validation_result
            new_entry = WeatherEntry(date_obj, temperature, description, precipitation)
            self.weather_entries.append(new_entry)
            self.update_treeview()
            self.clear_input_fields()
            messagebox.showinfo("Успех", "Запись добавлена!")

    def clear_input_fields(self):
        self.date_entry.set_date(datetime.now())
        self.temp_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.precip_combobox.set("Нет")
        self.tree.selection_remove(self.tree.selection())
        self.btn_delete.config(state=tk.DISABLED) # Отключаем кнопку удаления

    def update_treeview(self, entries_to_display=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        display_list = entries_to_display if entries_to_display is not None else self.weather_entries

        for entry in display_list:
            precip_str = "Да" if entry.precipitation else "Нет"
            self.tree.insert("", tk.END, values=(entry.date.strftime('%Y-%m-%d'), f"{entry.temperature:.1f}", entry.description, precip_str))

    def apply_filters(self):
        try:
            filter_date_str = self.filter_date_entry.get_date().strftime('%Y-%m-%d')
            filter_date_obj = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showwarning("Ошибка фильтра", "Некорректный формат даты для фильтра.")
            return

        filter_temp_str = self.filter_temp_entry.get().strip()
        min_temp = None
        if filter_temp_str:
            try:
                min_temp = float(filter_temp_str)
            except ValueError:
                messagebox.showwarning("Ошибка фильтра", "Температура для фильтра должна быть числом.")
                return

        filtered_list = self.weather_entries
        filtered_list = [entry for entry in filtered_list if entry.date.date() == filter_date_obj]
        if min_temp is not None:
            filtered_list = [entry for entry in filtered_list if entry.temperature > min_temp]

        self.update_treeview(filtered_list)

    def reset_filters(self):
        self.filter_date_entry.set_date(datetime.now())
        self.filter_temp_entry.delete(0, tk.END)
        self.update_treeview()

    def on_entry_select(self, event):
        if self.tree.selection():
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.btn_delete.config(state=tk.DISABLED)

    def delete_selected_entry(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите запись для удаления.")
            return

        if messagebox.askyesno("Подтверждение удаления", "Вы уверены, что хотите удалить выбранную запись?"):
            selected_item_id = selected_items[0]
            item_values = self.tree.item(selected_item_id)['values']
            
            entry_to_remove = None
            for entry in self.weather_entries:
                precip_str = "Да" if entry.precipitation else "Нет"
                if (entry.date.strftime('%Y-%m-%d') == item_values[0] and
                    f"{entry.temperature:.1f}" == item_values[1] and
                    entry.description == item_values[2] and
                    precip_str == item_values[3]):
                    entry_to_remove = entry
                    break
            
            if entry_to_remove:
                self.weather_entries.remove(entry_to_remove)
                self.update_treeview()
                self.clear_input_fields()
                messagebox.showinfo("Успех", "Запись успешно удалена.")
            else:
                messagebox.showerror("Ошибка", "Не удалось найти выбранную запись.")

    def clear_all_entries(self):
        if not self.weather_entries:
            messagebox.showinfo("Информация", "Список записей пуст.")
            return

        if messagebox.askyesno("Подтверждение очистки", "Вы уверены, что хотите удалить ВСЕ записи? Это действие нельзя отменить."):
            self.weather_entries.clear()
            self.update_treeview()
            self.clear_input_fields()
            self.reset_filters()
            messagebox.showinfo("Успех", "Все записи удалены.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDiaryApp(root)
    root.mainloop()
