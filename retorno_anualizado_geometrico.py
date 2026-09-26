def walk_forward(algorithm, data, n_folds=5, train_frac=0.6):
    """Retorna métricas por fold + 'stability' = 1 − std/|mean| de Sharpe."""