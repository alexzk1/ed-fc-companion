import tkinter as tk
import sys
import os
import gc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "EDMarketConnector"))
from ui_multy_planes_widget import MultiPlanesWidget, PlaneSwitch


def build_planes():
    return [
        PlaneSwitch("Первая", tooltip="Первая панель"),
        PlaneSwitch("Вторая", tooltip="Вторая панель"),
        PlaneSwitch("Третья", tooltip="Третья панель"),
    ]


def debug_refs(clsname):  # type: ignore
    for obj in gc.get_objects():
        if obj.__class__.__name__ == clsname:
            print(f"--- {clsname} instance: {obj} ---")
            refs = gc.get_referrers(obj)
            for r in refs:
                print("   ↳", type(r), r)  # type: ignore


def print_memory_stats():
    gc.collect()
    all_objs = gc.get_objects()

    def size_sum(clsname):
        objs = [o for o in all_objs if o.__class__.__name__ == clsname]
        total_size = sum(sys.getsizeof(o) for o in objs)
        return len(objs), total_size

    tooltip_count, tooltip_size = size_sum("Tooltip")
    multi_count, multi_size = size_sum("MultiPlanesWidget")

    print("=" * 40)
    print(f"Всего объектов в памяти: {len(all_objs)}")
    print(f"Tooltip: {tooltip_count} шт, ~{tooltip_size} байт")
    print(f"MultiPlanesWidget: {multi_count} шт, ~{multi_size} байт")
    print("=" * 40)


def recreate_widget(root, container):  # type: ignore
    for child in container.winfo_children():
        child.destroy()

    gc.collect()

    mpw = MultiPlanesWidget(build_planes(), container)  # type: ignore
    mpw.grid(row=0, column=0, sticky=tk.NSEW)

    print_memory_stats()


def main():
    root = tk.Tk()
    root.title("Тест MultiPlanesWidget")
    root.geometry("400x300")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    container = tk.Frame(root)
    container.grid(row=0, column=0, sticky=tk.NSEW)
    container.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)

    btn_frame = tk.Frame(root)
    btn_frame.grid(row=1, column=0, sticky=tk.EW)

    tk.Button(
        btn_frame, text="Пересоздать", command=lambda: recreate_widget(root, container)
    ).pack(side=tk.LEFT)

    recreate_widget(root, container)

    root.mainloop()


if __name__ == "__main__":
    main()
