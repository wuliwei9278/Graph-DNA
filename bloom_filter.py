#import h5py
import random
import time
from pybloom import BloomFilter
from scipy.io import loadmat
#from hdf5storage import savemat
from scipy.sparse import find

#data = "G_douban"
#data = "G_flixster"
#data = "citeseer"
#data = "training_test_dataset_yahoo_bf"
#data = "training_test_dataset_yahoo_nips"
data = "training_test_dataset_flixster"
#data = "training_test_dataset_douban" 

# load sparse graph matrix
x = loadmat(data + ".mat")
#x = loadmat("citeseer.mat")
#x = loadmat("cora.mat")
#x = loadmat("pubmed")
#x = loadmat("nell.mat")
#G = x['Gi']
G = x['Gu']

# number of nodes
n = G.shape[0]

# write G in node2vec format
with open("flixster-u.edgelist", 'w') as fw:
    for i in range(n):
        row_idx, _, _ = find(G[:, i])
        for j in row_idx:
            line = "{0} {1}\n".format(i + 1, j + 1)
            fw.write(line)

# capcicity in bloom filters
#cap = 1500
#cap = 500
#cap = 200
cap = 100
#cap = 60
#cap = 50
#cap = 10

# create bloom filters
f_list = []
num_fails = 0
for i in range(n):
    # num_bits is determined by capacity and error_rate
    f_i = BloomFilter(capacity=cap, error_rate=0.1)
    fail_or_not = f_i.add(i)
    if fail_or_not: num_fails += 1
    f_list.append(f_i)

# store snapshoots for each f_list
f_matrix = []
f_matrix.append([])
f_matrix.append(f_list)

# depth of graph we want to explore
depth = 2
#depth = 2
output_file = "{0}_bf{1}_nips.dat".format(data, depth)

start = time.time()
# create bipartite graph G' based on G
for d in range(depth):
    # obtain last snapshoot
    f_list = f_matrix[-1]
    new_f_list = []
    for i in range(n):
        f_i = f_list[i]  # bloom filter for node i
        row_idx, _, _ = find(G[:, i])
        
	    # check 
        k = f_i.num_bits
        bits = f_i.bitarray
        bits_str = str(bits)[10:10 + k]
        cnt = 0
        for j in range(len(bits_str)):
            if bits_str[j] == '1':
                cnt += 1
        if i < 10:
            print(d + 1, cnt)
        #if cnt > 500:
        #    new_f_list.append(f_i)
        #    continue 
	    # want to take union for each edge i ~ j
        random.shuffle(row_idx) 
        cnt = 0
        for j in row_idx:
            if cnt > 50 and depth >= 1:
	            continue
            # bloom filter for node j
            f_j = f_list[j]
            f_i = f_i.union(f_j)
            cnt += 1
        # create new bloom filter for node i
        new_f_list.append(f_i)
    #f_matrix.append(new_f_list)
    f_matrix[0] = f_matrix[1]
    f_matrix[1] = new_f_list

end = time.time()
print(end - start)
#assert len(f_matrix) == depth + 1
assert len(f_matrix) == 2

f_list = f_matrix[-1]
k = f_list[0].num_bits
print("number of nodes " + str(n))
print("number of bits for each node " + str(k))  # k = 2880


# create sparse adj matrix for G
row = []
col = []
val = []
for i in range(n):
    bits = f_list[i].bitarray
    bits_str = str(bits)[10:10 + k]
    for j in range(len(bits_str)):
        if bits_str[j] == '1':
            row.append(i + 1.0)
            col.append(j + 1.0)
            val.append(1.0)

print("number of non-zero elements is " + str(len(row)))
ratio_nnz = len(row) / float(n * k)
print("ratio of nnz is " + str(ratio_nnz))

#res = {"row": row, "col": col, "val": val, "n": n, "k": k}


#with open("bloom_pubmed_depth2.dat", 'w') as f:
#with open("bloom_cora_depth2.dat", 'w') as f:
#with open("bloom_pubmed_depth3.dat", 'w') as f:
with open(output_file, 'w') as f:
    for i in range(len(row)):
        line = "{0},{1},{2}\n".format(row[i], col[i], val[i])
        f.write(line)


