import csv
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import re
from numpy.lib.stride_tricks import sliding_window_view
#https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html

#https://www.codegenes.net/blog/pytorchnnue/


data = []
with open("training_cleaned.csv", "r", encoding="utf-8") as f:
    next(f)  # skip header
    for line in f:
        line = line.strip().strip('"')
        match = re.match(
            r'^([^ ]+ [bw]),"\(([^)]+)\)",([+-]?\d+)(?:,([+-]?\d+))?$',
            line)
        if match:
            fen = match.group(1)
            action = "(" + match.group(2) + ")"
            score = match.group(3)
            result = match.group(4)
            data.append([fen, action, score, result])
        else:
            print(f"Problemzeile (Parsing-Fehler): {line}")


df = pd.DataFrame(data, columns=["fen", "action", "score", "result"])
print(df.head())

def split_fen_turn(fen_str):
    parts = fen_str.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return parts[0], "b"
    

splitted = df["fen"].apply(lambda x: split_fen_turn(str(x)))
lengths = splitted.apply(lambda x: len(x) if hasattr(x, "__len__") else 0)
print(lengths.value_counts())
print(splitted[lengths != 2])
df[["fen_clean", "turn"]] = pd.DataFrame(splitted.tolist(), index=df.index)

def count_windows(board, player, n):
    count = 0
    board = np.array(board).reshape(8,8)
    # horizontal
    for row in board:
        for window in sliding_window_view(row, 4):
            if np.sum(window == player) == n and np.sum(window != 0) == n:
                count += 1
    # vertically
    for col in board.T:
        for window in sliding_window_view(col, 4):
            if np.sum(window == player) == n and np.sum(window != 0) == n:
                count += 1
    # diagonal \ + /
    for r in range(8-3):
        for c in range(8-3):
            diag1 = [board[r+i, c+i] for i in range(4)]
            diag2 = [board[r+3-i, c+i] for i in range(4)]
            if np.sum(np.array(diag1) == player) == n and np.sum(np.array(diag1) != 0) == n:
                count += 1
            if np.sum(np.array(diag2) == player) == n and np.sum(np.array(diag2) != 0) == n:
                count += 1
    return count


def parse_board_string(board_str):
    rows = board_str.split("/")
    board = []
    for row in rows:
        for char in row:
            if char.isdigit():
                board.extend([0] * int(char))
            elif char == "w":
                board.append(1)
            elif char == "b":
                board.append(-1)
    if len(board) != 64:
        print(f"WARNUNG: Board hat {len(board)} Felder statt 64! Board: {board_str}")
    return board

boards = [parse_board_string(fen) for fen in df["fen_clean"]]

pattern_features = []
for b in boards:
    pf = []
    for player in [1, -1]:
        pf.append(count_windows(b, player, 2))
        pf.append(count_windows(b, player, 3))
        pf.append(count_windows(b, player, 4))
    pattern_features.append(pf)
pattern_features = np.array(pattern_features)

turns = np.array([-1 if t.strip() == "b" else 1 for t in df["turn"]], dtype=np.float32).reshape(-1, 1)


scores = [float(s) for s in df["score"]]
y = np.array(scores, dtype=np.float32).reshape(-1, 1)


X = np.hstack((boards, turns, pattern_features))
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

dataset = TensorDataset(X_tensor, y_tensor)
loader = DataLoader(dataset, batch_size=64, shuffle=True)
#https://www.geeksforgeeks.org/machine-learning/how-to-choose-batch-size-and-number-of-epochs-when-fitting-a-model/


class Connect4NNUE(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(71, 48)
        #https://www.heatonresearch.com/2017/06/01/hidden-layers.html
        self.fc2 = nn.Linear(48, 32)
        #https://cris.brighton.ac.uk/ws/files/460869/ThomasEANN2017Final.pdf
        self.fc3 = nn.Linear(32, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = torch.tanh(self.fc3(x))
        #https://www.datacamp.com/tutorial/introduction-to-activation-functions-in-neural-networks
        #https://www.baeldung.com/cs/sigmoid-vs-tanh-functions
        return x

model = Connect4NNUE()
# loss function and optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01) # 0.001 lr=learning rate
epochs = 50
#https://www.geeksforgeeks.org/machine-learning/how-to-choose-batch-size-and-number-of-epochs-when-fitting-a-model/

for epoch in range(epochs):
    epoch_loss = 0.0
    for input_data, batch_y in loader:
        optimizer.zero_grad()
        output = model(input_data)

        target = batch_y / 100.0

        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss/len(loader):.6f}")

torch.save(model.state_dict(), "connect4_nnue_weights.pth")
model_export = Connect4NNUE()
state = torch.load("connect4_nnue_weights.pth")
print(type(state))
model_export.load_state_dict(state)
model_export.eval()
print(next(model.parameters()))
y_pred = model(torch.tensor(X, dtype=torch.float32))
print(y_pred)


dummy_input = torch.randn(1, 71) 
# Export
torch.onnx.export(model, dummy_input, "connect4_nnue_weights.onnx",
                  input_names=['input'], output_names=['output'],
                  opset_version=11)

print("Training completed and weights saved.")
#https://www.geeksforgeeks.org/machine-learning/convert-pytorch-model-to-tf-lite-with-onnx-tf/
