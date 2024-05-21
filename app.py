from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.h2("Hello Shiny for Python!"),
    ui.input_text("name", "What's your name?", ""),
    ui.output_text_verbatim("greeting")
)

def server(input, output, session):
    @output
    @render.text
    def greeting():
        return f"Hello, {input.name()}!"

app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)