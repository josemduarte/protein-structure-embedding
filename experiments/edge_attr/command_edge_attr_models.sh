python train_pst.py model.use_edge_attr=true model.gnn_type=gine logs.prefix=logs_pst/edge_attr_true
python train_pst.py model.use_edge_attr=false model.gnn_type=gin logs.prefix=logs_pst/edge_attr_false
