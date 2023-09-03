import customtkinter
from PIL import Image
import chatbot as chatbot

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()
root.title("ChatBot NBA")
root.geometry("900x500")
root.resizable(False, False)


def mostrar_mensaje(mensaje, usuario):
    texto_frame = customtkinter.CTkFrame(master=frame_chat, height=50, fg_color="transparent")
    if usuario == "usuario":
        texto_label = customtkinter.CTkLabel(master=texto_frame, text=mensaje, font=("Roboto", 16),
                                             width=70, height=25, corner_radius=20, fg_color="#007EF9")
        texto_label.pack(pady=12, padx=10, ipady=10, side="right",fill="both")
    else:
        texto_label = customtkinter.CTkLabel(master=texto_frame, text=mensaje, font=("Roboto", 16), justify="left",
                                             height=35, corner_radius=20, fg_color="#32E2B2",
                                             text_color="black")
        texto_label.pack(pady=12, padx=10, ipady=10, side="left")
    texto_frame.pack(pady=10, padx=10, fill="x", expand=True)


def enviar_mensaje():
    mostrar = "Tú: "
    texto = caja_ingreso.get()
    mostrar_mensaje(mostrar + texto, "usuario")
    print(texto)
    respuesta_chat(texto)
    caja_ingreso.delete(0, "end")


def respuesta_chat(entrada):
    mostrar = "ChatBot: "
    respuesta = chatbot.ingreso(entrada)
    mostrar_mensaje(mostrar + respuesta, "chatbot")


def salir():
    root.destroy()


frame_lateral = customtkinter.CTkFrame(master=root)
frame_lateral.pack(side="left", padx=10, pady=10, fill="both")
label = customtkinter.CTkLabel(master=frame_lateral, text="OPCIONES", font=("Roboto", 24))
label.pack(pady=30, padx=10)


# Boton salir
img_salir = customtkinter.CTkImage(dark_image=Image.open("img_salir.png"), size=(25, 25))
button_salir = customtkinter.CTkButton(master=frame_lateral, corner_radius=0, height=40, border_spacing=10,
                                            text="SALIR", image=img_salir, compound="left",
                                            command=salir, fg_color="transparent", text_color=("gray10", "gray90"),
                                            hover_color=("gray70", "gray30"), anchor="w")
button_salir.pack(pady=12, padx=10)

# FRAME CHAT
frame_principal = customtkinter.CTkFrame(master=root)
frame_principal.pack(padx=10, pady=10, fill="both", expand=True)

logo = customtkinter.CTkImage(dark_image=Image.open("logo.png"), size=(150, 100))
label_chat = customtkinter.CTkLabel(master=frame_principal, text="CHATBOT NBA   ", font=("Roboto", 50), image=logo, compound="right")
label_chat.pack(pady=12, padx=10, ipadx=10, ipady=10)

# caja de texto del chat
frame_chat = customtkinter.CTkScrollableFrame(master=frame_principal)
frame_chat.pack(padx=10, pady=10, fill="both", expand=True)

# caja de texto para escribir
caja_ingreso = customtkinter.CTkEntry(master=frame_principal, placeholder_text="Escribe tu mensaje", width=600, height=50)
caja_ingreso.pack(pady=12, padx=10, side="left")

# boton enviar
button_enviar = customtkinter.CTkButton(master=frame_principal, text="Enviar", command=enviar_mensaje, height=50)
button_enviar.pack(pady=12, padx=10, side="right")

root.mainloop()

