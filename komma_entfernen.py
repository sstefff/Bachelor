input_file = "training_neu.csv"  
output_file = "training_cleaned.csv"  # Ausgabe ohne Komma

with open(input_file, "r") as fin, open(output_file, "w") as fout:
    for line in fin:
        fout.write(line.rstrip().rstrip(',') + '\n')
