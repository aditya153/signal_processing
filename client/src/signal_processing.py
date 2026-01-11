import zmq
import numpy as np
from gen import waveform_pb2
import matplotlib.pyplot as plt
from scipy import signal as sig
from py3gpp import nrOFDMDemodulate

# Constants
SAMPLE_RATE = 122.88e6  # Hz


def iq_to_complex(iq_bytes):

    iq = np.frombuffer(iq_bytes, dtype=np.int16)
    return iq[0::2] + 1j * iq[1::2]

def synchronize_signals(tx, rx):

    corr = sig.correlate(rx, tx, mode='full')
    delay = np.argmax(np.abs(corr)) - len(tx) + 1
    
    if delay > 0:
        return tx[:-delay] if delay < len(tx) else tx, rx[delay:], delay
    elif delay < 0:
        return tx[-delay:], rx[:delay], delay
    return tx, rx, delay

def ofdm_demodulate(signal, fs):

    class carrier:
        NCellID = 1
        NSizeGrid = 275
        SubcarrierSpacing = 30
        SymbolsPerSlot = 14      
        SlotsPerSubframe = 2       
        CyclicPrefix = 'normal'    
    
    return nrOFDMDemodulate(carrier(), signal, fs)

def estimate_channel(tx_grid, rx_grid):
    epsilon = 1e-10
    H = rx_grid / (tx_grid + epsilon)
    mask = np.abs(tx_grid) > 0.01 * np.max(np.abs(tx_grid))
    H = np.where(mask, H, 0)  
    H_avg = np.mean(H, axis=1)
    return np.abs(H_avg), np.angle(H_avg)

def main():
    # Initialize ZMQ
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("ipc:///tmp/comsock")
    
    print("Connected to server. Waiting for waveforms...")
    
    tx_signal = None
    rx_signal = None
    
    try:
        while True:
            # Receive and parse protobuf message
            message = socket.recv()
            msg = waveform_pb2.Waveform()
            msg.ParseFromString(message)
            

            if msg.name not in ("tx", "rx"):
                continue
            
            # Convert IQ bytes to complex signal
            signal = iq_to_complex(msg.iq_samples)
            
            if msg.name == "tx":
                tx_signal = signal
                print(f"TX received: {len(signal)} samples")
            elif msg.name == "rx":
                rx_signal = signal
                print(f"RX received: {len(signal)} samples")
            
            if tx_signal is not None and rx_signal is not None:
                print("Both signals received. Processing...")
                
                # Subtask 1: Transmit and receive signlas side by side time domain graph
                num_samples = len(tx_signal)  # 30752
                t = np.arange(num_samples) / SAMPLE_RATE  

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

                # Left plot: TX
                ax1.plot(t * 1e6, tx_signal.real)  # Convert to microseconds
                ax1.set_xlabel('Time (μs)')
                ax1.set_ylabel('Amplitude')
                ax1.set_title('TX Signal (Transmitted)')
                # Right plot: RX
                ax2.plot(t * 1e6, rx_signal.real)
                ax2.set_xlabel('Time (μs)')
                ax2.set_ylabel('Amplitude')
                ax2.set_title('RX Signal (Received)')

                plt.tight_layout()  
                plt.savefig('results/task1.png', dpi=150)
                plt.close()
                print("Task 1 Completed results/task1.png saved successfully")
                

                # Subtask 2: Synchronize and overlay
                tx_sync, rx_sync, delay = synchronize_signals(tx_signal, rx_signal)
                t = np.arange(len(tx_sync)) / SAMPLE_RATE
                plt.figure(figsize=(12, 4))
                plt.plot(t * 1e6, tx_sync.real, label='TX', alpha=0.7)
                plt.plot(t * 1e6, rx_sync.real, label='RX (synced)', alpha=0.7)
                plt.xlabel('Time (μs)')
                plt.ylabel('Amplitude')
                plt.title('TX and Synchronized RX')
                plt.legend()
                plt.tight_layout()
                plt.savefig('results/task2.png', dpi=150)
                plt.close()
                print(f"Task 2 Completed: delay = {delay} samples")

                # Subtask 3: OFDM Demodulation
                tx_grid = ofdm_demodulate(tx_sync, SAMPLE_RATE)
                rx_grid = ofdm_demodulate(rx_sync, SAMPLE_RATE)
            
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

                ax1.imshow(np.abs(tx_grid), aspect='auto', origin='lower', cmap='viridis')
                ax1.set_xlabel('OFDM Symbol')
                ax1.set_ylabel('Subcarrier')
                ax1.set_title('TX OFDM Grid')
                plt.colorbar(ax1.images[0], ax=ax1)

                ax2.imshow(np.abs(rx_grid), aspect='auto', origin='lower', cmap='viridis')
                ax2.set_xlabel('OFDM Symbol')
                ax2.set_ylabel('Subcarrier')
                ax2.set_title('RX OFDM Grid')
                plt.colorbar(ax2.images[0], ax=ax2)
            
                plt.tight_layout()
                plt.savefig('results/task3.png', dpi=150)
                plt.close()
                print(f"Task 3 Completed: TX {tx_grid.shape}, RX {rx_grid.shape}")

                # Subtask 4: Channel Estimation
                amplitude, phase = estimate_channel(tx_grid, rx_grid)
                subcarriers = np.arange(len(amplitude))

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

                ax1.plot(subcarriers, amplitude)
                ax1.set_xlabel('Subcarrier Index')
                ax1.set_ylabel('Amplitude')
                ax1.set_title('Channel Amplitude Response')
                ax1.grid(True, alpha=0.3)

                ax2.plot(subcarriers, phase)
                ax2.set_xlabel('Subcarrier Index')
                ax2.set_ylabel('Phase (radians)')
                ax2.set_title('Channel Phase Response')
                ax2.grid(True, alpha=0.3)

                plt.tight_layout()
                plt.savefig('results/task4.png', dpi=150)
                plt.close()
                print(f"Task 4 Completed: Channel estimated for {len(amplitude)} subcarriers")
                break

    except KeyboardInterrupt:
        print("\nStopping client...")
    finally:
        socket.close()
        context.term()
        print("Done!")

if __name__ == "__main__":
    main()