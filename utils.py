import torch.nn.functional as F
import numpy as np
from sklearn.metrics import roc_curve
from sklearn.metrics import auc


def load_data(rna_dis_adj, k_folds):
    test_pos_list = list()
    test_pos_idx = np.array(np.where(rna_dis_adj == 1))
    test_neg_idx = np.array(np.where(rna_dis_adj == 0))
    rng = np.random.default_rng()
    rng.shuffle(test_pos_idx, axis=1)

    for test_pos in np.array_split(test_pos_idx, k_folds, axis=1):
        num_of_samples = len(test_pos[0])

        rng.shuffle(test_neg_idx, axis=1)
        test_neg = test_neg_idx[:, :num_of_samples]
        test_pos_list.append(np.hstack((test_pos, test_neg)))
    return test_pos_list


def normalize_mat(mat):
    assert mat.size != 0, f"Calculating normalized matrix need a non-zero square matrix. matrix size:{mat.shape}"
    mat_size = mat.shape[0]
    diag = np.zeros((mat_size, mat_size))
    np.fill_diagonal(diag, np.power(np.sum(mat, axis=0), -1/2))
    ret = diag.dot(mat).dot(diag)
    return ret


def construct_het_graph(rna_dis_mat, dis_mat, miu):
    # 计算RNA相似度矩阵
    num_of_rna = rna_dis_mat.shape[0]
    out_degree_vec = np.sum(rna_dis_mat, axis=1)
    out_degree_mat = out_degree_vec[:, None] + out_degree_vec
    dis_sim_vec = np.zeros(num_of_rna)
    for i in range(num_of_rna):
        dis_idx = np.where(rna_dis_mat[i] == 1)[0]
        sum_dis_sim = 0
        for row in dis_idx:
            maximum = 0
            for col in dis_idx:
                if dis_mat[row][col] > maximum:
                    maximum = dis_mat[row][col]
            sum_dis_sim += maximum
        dis_sim_vec[i] = sum_dis_sim
    rna_mat = np.divide(dis_sim_vec[:, None] + dis_sim_vec, out_degree_mat, where=(out_degree_mat != 0))

    mat1 = np.hstack((rna_mat * miu, rna_dis_mat))
    mat2 = np.hstack((rna_dis_mat.T, dis_mat * miu))
    ret = np.vstack((mat1, mat2))
    return ret


def construct_adj_mat(training_mask):
    adj_tmp = training_mask.copy()
    adj_tmp = (1 - adj_tmp) * -1e9
    rna_mat = np.zeros((training_mask.shape[0], training_mask.shape[0]))
    dis_mat = np.zeros((training_mask.shape[1], training_mask.shape[1]))

    mat1 = np.hstack((rna_mat, adj_tmp))
    mat2 = np.hstack((adj_tmp.T, dis_mat))
    ret = np.vstack((mat1, mat2))
    return ret


# rna_dis_adj_mat, pred_adj_mat, training_mat类型为numpy.array
"""
def calculate_auc(rna_dis_adj_mat, pred_adj_mat, training_mat):
    pred_adj_mat = np.reshape(pred_adj_mat, (713, 447))
    idx = np.where(training_mat == 0)
    truth_score = rna_dis_adj_mat[idx]
    pred_score = pred_adj_mat[idx]
    fpr, tpr, thresholds = roc_curve(truth_score, pred_score)
    ret = auc(fpr, tpr)
    return ret
"""
def calculate_auc(rna_dis_adj_mat, pred_adj_mat, testing_data_idx):
    pred_adj_mat = np.reshape(pred_adj_mat, (rna_dis_adj_mat.shape[0], rna_dis_adj_mat.shape[1]))
    row_idx = testing_data_idx[0]
    col_idx = testing_data_idx[1]
    truth_score = rna_dis_adj_mat[row_idx, col_idx]
    pred_score = pred_adj_mat[row_idx, col_idx]
    fpr, tpr, thresholds = roc_curve(truth_score, pred_score)
    ret = auc(fpr, tpr)
    return ret


def calculate_loss(pred, label, norm, pos_weight):
    return norm * F.binary_cross_entropy_with_logits(pred, label, pos_weight=pos_weight, reduction="mean")
