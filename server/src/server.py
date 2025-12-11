import time
import zmq
from datetime import datetime, timezone
from gen import waveform_pb2

context = zmq.Context()
serv_sock = context.socket(zmq.PUSH)
serv_sock.setsockopt(zmq.CONFLATE, 1)
serv_sock.bind("ipc:///tmp/comsock")

# Load waveforms once
def load_waveform(filename):
    with open(filename, "rb") as f:
        return f.read()  # send raw bytes

tx_bytes = load_waveform("samples/txWaveform.dat")
rx_bytes = load_waveform("samples/rxWaveform.dat")

while True:
    for name, buf in [("tx", tx_bytes), ("rx", rx_bytes)]:
        msg = waveform_pb2.Waveform()
        msg.name = name
        timestamp = datetime.now(timezone.utc).timestamp()
        msg.timestamp = int(timestamp)
        msg.iq_samples = buf                      
        serv_sock.send(msg.SerializeToString())
        print(f"{timestamp}: Sent {name} waveform ({len(buf)} bytes)")
    time.sleep(1)  
