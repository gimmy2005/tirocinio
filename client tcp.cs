using UnityEngine;
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine.SceneManagement;
using System.Collections;

public class Client : MonoBehaviour
{
    public string serverAddress = "127.0.0.1";
    public int serverPort = 12345;

    private TcpClient client;
    private NetworkStream stream;
    private Thread receiveThread;
    private volatile bool isRunning = true;
    private volatile int ACTUALSCENE = 1;
    private int previousScene = -1;
    private volatile bool sceneChanged = false;

    void Awake()
    {
        DontDestroyOnLoad(this.gameObject);
    }

    void Start()
    {
        StartCoroutine(LoadInitialScene());
    }

    IEnumerator LoadInitialScene()
    {
        ConnectToServer();
        StartCoroutine(SceneUpdater());
        yield return null;
    }

    void ConnectToServer()
    {
        try
        {
            client = new TcpClient();
            client.Connect(serverAddress, serverPort);
            stream = client.GetStream();
            Debug.Log("Connected to server.");

            SendMessageToServer("READY");

            receiveThread = new Thread(ReceiveMessages);
            receiveThread.Start();
        }
        catch (Exception e)
        {
            Debug.LogError($"Error connecting to server: {e}");
            CloseConnection();
        }
    }

    void ReceiveMessages()
    {
        while (isRunning)
        {
            try
            {
                byte[] lengthBytes = new byte[4];
                int bytesRead = stream.Read(lengthBytes, 0, lengthBytes.Length);
                if (bytesRead == 0)
                {
                    Debug.LogWarning("Server closed the connection.");
                    CloseConnection();
                    return;
                }

                if (BitConverter.IsLittleEndian)
                {
                    Array.Reverse(lengthBytes);
                }

                int messageLength = BitConverter.ToInt32(lengthBytes, 0);
                byte[] messageBytes = new byte[messageLength];
                bytesRead = stream.Read(messageBytes, 0, messageLength);

                if (bytesRead == 0)
                {
                    Debug.LogWarning("Server closed the connection.");
                    CloseConnection();
                    return;
                }

                string message = Encoding.UTF8.GetString(messageBytes, 0, bytesRead);
                Debug.Log($"Received message: {message}");

                if (message == "FINE")
                {
                    CloseConnection();
                    return;
                }

                int newScene;
                if (int.TryParse(message, out newScene))
                {
                    lock (this)
                    {
                        ACTUALSCENE = newScene;
                        sceneChanged = true;
                    }
                }

                SendMessageToServer("OK");
            }
            catch (Exception e)
            {
                if (isRunning)
                {
                    Debug.LogError($"Error receiving message: {e}");
                }
                CloseConnection();
                return;
            }
        }
        Debug.Log("Receive thread exiting.");
    }

    void SendMessageToServer(string message)
    {
        byte[] messageBytes = Encoding.UTF8.GetBytes(message);
        byte[] lengthPrefix = BitConverter.GetBytes(messageBytes.Length);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(lengthPrefix);
        }

        try
        {
            stream.Write(lengthPrefix, 0, lengthPrefix.Length);
            stream.Write(messageBytes, 0, messageBytes.Length);
            Debug.Log($"Sent message: {message}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Error sending message: {e}");
            CloseConnection();
        }
    }

    IEnumerator SceneUpdater()
    {
        while (isRunning)
        {
            lock (this)
            {
                if (sceneChanged && ACTUALSCENE != previousScene)
                {
                    previousScene = ACTUALSCENE;
                    sceneChanged = false;
                    StartCoroutine(ChangeScene(ACTUALSCENE));
                }
            }
            yield return null;
        }
    }

    IEnumerator ChangeScene(int sceneIndex)
    {
        Debug.Log($"Caricamento della scena {sceneIndex}...");
        AsyncOperation asyncLoad = SceneManager.LoadSceneAsync(sceneIndex);
        while (!asyncLoad.isDone)
        {
            yield return null;
        }
        Debug.Log($"Scena {sceneIndex} caricata!");
        yield return new WaitForSeconds(3f);
    }

    void OnDestroy()
    {
        CloseConnection();
    }

    void CloseConnection()
    {
        if (!isRunning) return;
        isRunning = false;

        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Join();
        }

        if (stream != null)
        {
            stream.Close();
            stream = null;
        }
        if (client != null)
        {
            client.Close();
            client = null;
        }

        Debug.Log("Connection closed.");
    }
}