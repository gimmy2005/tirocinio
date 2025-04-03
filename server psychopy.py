from psychopy import visual, core, event, gui
from pythonosc import udp_client, osc_server, dispatcher
from threading import Thread
import time

# Configurazione OSC
UNITY_IP = "192.168.1.161"  # Indirizzo IP del computer Unity
UNITY_PORT = 7001  # Porta su cui Unity ascolta
PYTHON_LISTEN_PORT = 12346  # Porta su cui Python ascolta per Unity

# Inizializzazione del client OSC
unity_client = udp_client.SimpleUDPClient(UNITY_IP, UNITY_PORT)

# Variabile per controllare se Unity è pronto
unity_is_ready = False

# Inizializzazione della finestra di PsychoPy
win = visual.Window([500, 500], monitor="default", units="norm", winType='pyglet')
win.flip()  # Rendere la finestra visibile (workaround per versioni precedenti)

# Funzione per gestire il messaggio "/unity_ready" da Unity
def unity_ready_handler(address, *args):
    global unity_is_ready
    if address == "/unity_ready":
        print("Server Python: Unity is ready for the next scene.")
        unity_is_ready = True

# Inizializzazione del dispatcher OSC
disp = dispatcher.Dispatcher()
disp.map("/unity_ready", unity_ready_handler)

# Avvio del server OSC in un thread separato
server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", PYTHON_LISTEN_PORT), disp)
print(f"Server Python: Listening for Unity on port {PYTHON_LISTEN_PORT}")
server_thread = Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

# Invia un messaggio iniziale a Unity per avviare la comunicazione
print("Server Python: Sending initial /request_next to Unity.")
unity_client.send_message("/request_next", 1)

# Variabili per tenere traccia dei numeri inseriti
entered_scene_numbers = set()
max_attempts = 4
attempts = 0

# Loop principale per chiedere l'input tramite finestra di PsychoPy e inviare i numeri di scena
try:
    while attempts < max_attempts:
        if unity_is_ready:
            unity_is_ready = False  # Resetta la flag

            myDlg = gui.Dlg(title=f"Inserisci il numero della scena ({attempts + 1}/{max_attempts})")
            myDlg.addField("Numero scena (1-4):")
            ok_data = myDlg.show()

            if myDlg.OK:
                try:
                    scene_number = int(ok_data[0])
                    if 1 <= scene_number <= 4:
                        if scene_number not in entered_scene_numbers:
                            print(f"Server Python: Sending scene number {scene_number} to Unity.")
                            unity_client.send_message("/scene_number", scene_number)
                            entered_scene_numbers.add(scene_number)
                            attempts += 1
                            print("Server Python: Waiting for Unity to load scene and be ready...")
                        else:
                            print("Server Python: This scene number has already been entered. Please enter a different number.")
                            unity_is_ready = True # Se il numero è duplicato, Unity non riceve nulla, quindi resta "pronto" per un nuovo input
                    else:
                        print("Server Python: Invalid scene number. Please enter a number between 1 and 4.")
                        unity_is_ready = True # Se l'input non è valido, Unity non riceve nulla, quindi resta "pronto" per un nuovo input
                except ValueError:
                    print("Server Python: Invalid input. Please enter an integer.")
                    unity_is_ready = True # Se l'input non è valido, Unity non riceve nulla, quindi resta "pronto" per un nuovo input
            else:
                # L'utente ha premuto "Cancel"
                print("Server Python: User cancelled the input.")
                break

        core.wait(0.1)  # Breve pausa

    if attempts == max_attempts:
        print("Server Python: All 4 unique scene numbers have been entered.")

except KeyboardInterrupt:
    print("\nServer Python: Exiting.")
finally:
    server.shutdown()
    server_thread.join()
    win.close()
