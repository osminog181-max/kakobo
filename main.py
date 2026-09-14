from app import KekoboApp

if __name__ == "__main__":
    app = KekoboApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
#готово