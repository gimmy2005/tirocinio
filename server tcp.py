import socket
import random
import time
import traceback

def send_message(message, connection):
    """Invia un messaggio e attende una conferma."""
    try:
        message_bytes = message.encode('utf-8')
        connection.sendall(len(message_bytes).to_bytes(4, 'big'))
        connection.sendall(message_bytes)
        print(f"Messaggio inviato: {message}")

        length_bytes = connection.recv(4)
        if not length_bytes:
            print("Errore: Nessuna conferma ricevuta dal client (lunghezza).")
            return False

        message_length = int.from_bytes(length_bytes, 'big')
        confirmation = connection.recv(message_length)
        if not confirmation:
            print("Errore: Nessuna conferma ricevuta dal client (conferma).")
            return False

        confirmation = confirmation.decode('utf-8')
        if confirmation == "OK":
            print("Conferma ricevuta dal client.")
            return True
        else:
            print(f"Errore: Conferma non valida ricevuta: {confirmation}")
            return False

    except socket.error as e:
        print(f"Errore durante l'invio/ricezione (in send_message): {e}")
        return False
    except Exception as e:
        print(f"Errore non gestito in send_message: {e}\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    server_address = ('127.0.0.1', 12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)
    sock.listen(1)

    print("Server in attesa di connessioni...")

    try:
        while True:
            connection, client_address = sock.accept()
            print(f"Connessione stabilita da: {client_address}")
            try:
                length_bytes = connection.recv(4)
                if not length_bytes:
                    print("Errore: Nessun dato ricevuto (lunghezza READY).")
                    break

                message_length = int.from_bytes(length_bytes, 'big')
                data = connection.recv(message_length)
                if not data:
                    print("Errore: Nessun dato ricevuto (messaggio READY).")
                    break

                message = data.decode('utf-8')
                print(f"Messaggio ricevuto: {message}")

                if message == "READY":
                    print("Client pronto, invio messaggi ogni 5 secondi...")
                    scenes = [1, 2, 3, 4]
                    random.shuffle(scenes)
                    scene_index = 0

                    while True:
                        if scene_index < len(scenes):
                            message_to_send = str(scenes[scene_index])
                            scene_index += 1
                        else:
                            message_to_send = "FINE"

                        if not send_message(message_to_send, connection):
                            print("Errore in send_message, chiusura connessione.")
                            break

                        if message_to_send == "FINE":
                            break

                        time.sleep(5)

            except socket.error as e:
                print(f"Errore durante la ricezione/invio (nel ciclo principale): {e}")
            except Exception as e:
                print(f"Errore non gestito nel ciclo principale: {e}\n{traceback.format_exc()}")
            finally:
                connection.close()
                print("Connessione chiusa.")

            if message_to_send == "FINE":
                break

    except Exception as e:
        print(f"Errore principale del server: {e}\n{traceback.format_exc()}")
    finally:
        sock.close()
        print("Esperimento terminato e socket chiuso.")