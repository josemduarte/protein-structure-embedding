import os

import numpy as np
from numpy import dot
from numpy.linalg import norm

import pandas as pd

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import auc
import chromadb


class RcsbEmbeddingDataset:
    def __init__(
            self,
            embedding_dir,
            embedding_class_file
    ):
        chroma_client = chromadb.Client()
        self.db_collection = chroma_client.create_collection(
            name="chain_collection",
            metadata={"hnsw:space": "cosine"}
        )

        self.embedding_pairs = []
        self.embeddings = {}
        self.embeddings_classes = {}
        self.n_classes = {}
        self.embedding_dir = embedding_dir
        self.embedding_classe_file = embedding_class_file
        self.load_embedding()
        self.load_classes()
        super().__init__()

    def load_embedding(self):
        for file in os.listdir(self.embedding_dir):
            embedding_id = ".".join(file.split(".")[0:-2])
            v = list(pd.read_csv(f"{self.embedding_dir}/{file}").iloc[:, 0].values)
            self.db_collection.add(
                embeddings=[v],
                ids=[embedding_id]
            )
            self.embeddings[embedding_id] = v

    def load_classes(self):
        for row in open(self.embedding_classe_file):
            embedding_id = row.strip().split("\t")[0]
            embedding_class = row.strip().split("\t")[1]
            self.embeddings_classes[embedding_id] = embedding_class
            if embedding_class in self.n_classes:
                self.n_classes[embedding_class] += 1
            else:
                self.n_classes[embedding_class] = 1

    def load_embedding_pairs(self):
        ids = list(self.embeddings.keys())
        n_pos = 0
        n_neg = 0
        while len(ids) > 0:
            embedding_i = ids.pop()
            for embedding_j in ids:
                if embedding_i in self.embeddings_classes and embedding_j in self.embeddings_classes:
                    pred = 1 if self.embeddings_classes[embedding_i] == self.embeddings_classes[embedding_j] else 0
                    if pred == 1:
                        n_pos += 1
                    else:
                        n_neg += 1
                    self.embedding_pairs.append([
                        embedding_i,
                        embedding_j,
                        pred
                    ])
        print(f"Number of positives: {n_pos}, negatives: {n_neg}")

    def len(self):
        return len(self.embedding_pairs)

    def pairs(self):
        for embedding_pair in self.embedding_pairs:
            yield (
                self.embeddings[embedding_pair[0]],
                self.embeddings[embedding_pair[1]],
                embedding_pair[2]
            )

    def domains(self):
        for embedding_id in self.embeddings:
            yield embedding_id, self.embeddings[embedding_id]

    def query(self, val):
        return self.db_collection.query(val)

    def get_class(self, dom):
        return self.embeddings_classes[dom]

    def get_n_classes(self, name):
        return self.n_classes[name]


if __name__ == '__main__':
    dataloader = RcsbEmbeddingDataset(
        embedding_dir="/Users/joan/data/structure-embedding/pst_t30_so/scop40/embedding",
        embedding_class_file="/Users/joan/data/scop40pdb/scop40pdb_class.tsv"
    )
    x = []
    y = []
    for e_i, e_j, b in dataloader.pairs():
        e_i = np.squeeze(e_i)
        e_j = np.squeeze(e_j)
        p = dot(e_i, e_j) / (norm(e_i) * norm(e_j))
        x.append(p)
        y.append(b[0].item())

    precision, recall, thresholds = precision_recall_curve(y, x)
    pr_auc = auc(recall, precision)
    print(pr_auc)

    for d, v in dataloader.domains():
        print(d)
        results = dataloader.query(v)
        print([x for x in results['ids'][0]])
        print([dataloader.get_class(x) for x in results['ids'][0]])
        print(dataloader.get_n_classes(dataloader.get_class(d)))
