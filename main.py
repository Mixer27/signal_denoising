import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import filedialog, Tk, Label, Button, Entry, StringVar, OptionMenu, messagebox

def load_signal(file_path):
    try:
        return pd.read_csv(file_path, delimiter=';', header=None).values
    except Exception as e:
        messagebox.showerror("Błąd wczytywania pliku", str(e))
        return None

def save_signal(signal, file_path):
    try:
        pd.DataFrame(signal).to_csv(file_path, header=None, index=False, sep=';')
        messagebox.showinfo("Zapisano", f"Sygnał zapisany do {file_path}")
    except Exception as e:
        messagebox.showerror("Błąd zapisu pliku", str(e))

def plot_signal(signal, title, sampling_rate=None):
    try:
        plt.figure(figsize=(8, 4))
        if sampling_rate is not None:
            time = np.arange(signal.shape[0]) / sampling_rate
            plt.plot(time, signal)
            plt.xlabel('Czas (s)')
        else:
            plt.plot(signal)
            plt.xlabel('Próbki')
        plt.title(title)
        plt.ylabel('Amplituda')
        plt.grid(True)
        plt.show()
    except Exception as e:
        messagebox.showerror("Błąd wyświetlania wykresu", str(e))


def calculate_mu(N, mu_min=0.005, mu_max=0.1, N_min=100, N_max=1000):
    if N <= N_min:
        return mu_max
    elif N >= N_max:
        return mu_min
    else:
        mu_range = np.log(mu_max / mu_min)
        N_range = np.log(N_max / N_min)
        return mu_max * np.exp(-mu_range * (np.log(N / N_min) / N_range))

def nlms_filter(x, filter_order=4, epsilon=1e-6):
    N = len(x)
    mu = calculate_mu(N)
    w = np.zeros(filter_order)
    y = np.zeros(N)
    e = np.zeros(N)
    for n in range(filter_order, N):
        x_n = x[n:n-filter_order:-1]
        norm_x = np.dot(x_n, x_n) + epsilon
        y[n] = np.dot(w, x_n)
        e[n] = x[n] - y[n]
        w += (2 * mu * e[n] * x_n) / norm_x
    return y, e


def wiener_filter(signal, mysize=None, noise=None):
    if mysize is None:
        mysize = 3
    
    signal = np.asarray(signal)
    if noise is None:
        noise = np.var(signal)
    
    local_mean = np.convolve(signal, np.ones(mysize)/mysize, mode='same')
    
    local_var = np.convolve(signal**2, np.ones(mysize)/mysize, mode='same') - local_mean**2
    
    wiener_output = local_mean + (np.maximum(local_var - noise, 0) / np.maximum(local_var, noise)) * (signal - local_mean)
    
    return wiener_output

class SignalDenoiserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Usuwanie szumu z sygnałów")
        
        self.file_path = StringVar()
        self.method = StringVar(value="NLMS")
        self.samples = StringVar()
        self.sampling_rate = StringVar()
        self.signal = None
        self.filtered_signal = None
        
        Label(root, text="Ścieżka do pliku:").grid(row=0, column=0, padx=10, pady=5)
        Entry(root, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=10, pady=5)
        Button(root, text="Wczytaj plik", command=self.load_file).grid(row=0, column=2, padx=10, pady=5)
        
        Label(root, text="Liczba próbek:").grid(row=1, column=0, padx=10, pady=5)
        Entry(root, textvariable=self.samples, width=10).grid(row=1, column=1, padx=10, pady=5)
        
        Label(root, text="Próbkowanie:").grid(row=2, column=0, padx=10, pady=5)
        Entry(root, textvariable=self.sampling_rate, width=10).grid(row=2, column=1, padx=10, pady=5)
        
        Button(root, text="Wyświetl sygnał", command=self.display_signal).grid(row=3, column=0, columnspan=3, padx=10, pady=10)
        
        Label(root, text="Metoda odszumiania:").grid(row=4, column=0, padx=10, pady=5)
        OptionMenu(root, self.method, "NLMS", "Wiener").grid(row=4, column=1, padx=10, pady=5)
        
        Button(root, text="Wykonaj odszumianie", command=self.denoise_signal).grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        
        Button(root, text="Wyświetl odszumiony sygnał", command=self.display_denoised_signal).grid(row=6, column=0, columnspan=3, padx=10, pady=10)
        
        Button(root, text="Zapisz sygnał", command=self.save_denoised_signal).grid(row=7, column=0, columnspan=3, padx=10, pady=10)
        
    def load_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path.set(file_path)
            self.signal = load_signal(file_path)
            if self.signal is not None:
                self.samples.set(str(self.signal.shape[0]))
                messagebox.showinfo("Wczytano", "Plik wczytano pomyślnie!")
    
    def display_signal(self):
        if self.signal is not None:
            sampling_rate = float(self.sampling_rate.get()) if self.sampling_rate.get() else None
            plot_signal(self.signal, "Oryginalny sygnał", sampling_rate)
        else:
            messagebox.showerror("Błąd", "Nie wczytano sygnału.")
    
    def denoise_signal(self):
        if self.signal is not None:
            x = self.signal.flatten()
            if self.method.get() == "NLMS":
                y, _ = nlms_filter(x)
            else:
                y = wiener_filter(x)
            self.filtered_signal = y
            messagebox.showinfo("Odszumianie", "Odszumianie zakończone pomyślnie!")
        else:
            messagebox.showerror("Błąd", "Nie wczytano sygnału.")
    
    def display_denoised_signal(self):
        if self.filtered_signal is not None:
            sampling_rate = float(self.sampling_rate.get()) if self.sampling_rate.get() else None
            plot_signal(self.filtered_signal, "Odszumiony sygnał ({})".format(self.method.get()), sampling_rate)
        else:
            messagebox.showerror("Błąd", "Nie wykonano odszumiania.")
    
    def save_denoised_signal(self):
        if self.filtered_signal is not None:
            save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if save_path:
                save_signal(self.filtered_signal, save_path)
        else:
            messagebox.showerror("Błąd", "Nie wykonano odszumiania.")

if __name__ == "__main__":
    root = Tk()
    app = SignalDenoiserApp(root)
    root.mainloop()