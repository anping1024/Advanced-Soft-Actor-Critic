import algorithm.nn_models as m

ModelRep = m.ModelSimpleRep


class ModelQ(m.ModelQ):
    def _build_model(self):
        super()._build_model(c_dense_n=256, c_dense_depth=3)


class ModelPolicy(m.ModelPolicy):
    def _build_model(self):
        super()._build_model(c_dense_n=256, c_dense_depth=3,
                             mean_n=256, mean_depth=1,
                             logstd_n=256, logstd_depth=1)


class ModelRND(m.ModelRND):
    def _build_model(self):
        return super()._build_model(dense_n=128, dense_depth=2, output_size=128)
