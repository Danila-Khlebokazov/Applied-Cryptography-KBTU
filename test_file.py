import npyscreen


class MyForm(npyscreen.Form):
    def create(self):
        self.add(npyscreen.FixedText, value="Big Text Demo", editable=False, rely=2, relx=64, color="STANDOUT")
        self.add(npyscreen.FixedText, value="This is bigger text!", editable=False, rely=4, relx=30, color="BOLD")


class MyApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.addForm("MAIN", MyForm, name="Big Text Demo")


if __name__ == "__main__":
    app = MyApp()
    app.run()
