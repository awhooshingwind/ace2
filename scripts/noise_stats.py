import numpy as np
import matplotlib.pyplot as plt
import csv
import cv2
import os
import re

# Function to extract numerical part of the filename for proper sorting
def numerical_sort(value):
    # Extract digits from the filename and convert them to integers for sorting
    numbers = re.findall(r'\d+', value)
    return [int(num) for num in numbers]

counts = []
std_dev = []

with open('noise/stats.txt', 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        # print(row[2])
        counts.append(float(row[1]))
        std_dev.append(float(row[2]))


std_dev = np.array(std_dev)
std_dev_sq = std_dev**2

plt.scatter(counts, std_dev_sq)
fit = np.polyfit(counts, std_dev_sq, 1)
x_vals = np.linspace(0, np.max(counts), 100)
plt.plot(x_vals, x_vals*fit[0])


print(fit)


# plt.scatter(counts, np.asarray(std_dev)/np.sqrt(2))
# fig = plt.figure()
# plt.scatter(np.log(counts), np.log(np.asarray(std_dev)/np.sqrt(2)))
# plt.loglog(counts, np.asarray(std_dev)/np.sqrt(2))
plt.show()

# img_path = 'noise/0926'
# img_list = os.listdir(img_path)

# img_list.sort(key=numerical_sort)

# for i in range(0, len(img_list), 2):
#     img1 = cv2.imread(f'{img_path}/{img_list[i]}')
#     img2 = cv2.imread(f'{img_path}/{img_list[i+1]}')

#     print(np.count_nonzero(img1))
    
#     tmp_subtract = img1.astype(np.int16)-img2.astype(np.int16)
#     tmp_std_dev = np.std(tmp_subtract)/np.sqrt(2)
#     tmp_mean = np.mean(img1)
#     print(tmp_mean, tmp_std_dev)
#     plt.scatter(tmp_mean, tmp_std_dev)

# plt.show()
