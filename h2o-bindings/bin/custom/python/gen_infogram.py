rest_api_version = 3  # type: int

def update_param(name, param):
    if name == 'infogram_algorithm_params':
        param['type'] = 'KeyValue'
        param['default_value'] = None
        return param
    return None  # param untouched

def class_extensions():
    def plot(self, valid=False, xval=False, figsize=(10, 10), server=False):
        """
        Perform plot function of infogram.  This code is given to us by Tomas Fryda.  By default, it will plot the
        infogram calculated from training dataset.  Note that the frame rel_cmi_frame contains the following columns:
        - 0: predictor names
        - 1: admissible 
        - 2: admissible index
        - 3: relevance-index or total information
        - 4: safety-index or net information, normalized from 0 to 1
        - 5: safety-index or net information not normalized
        
        :param self: 
        :param valid: True if to plot infogram from validation dataset
        :param xval: True if to plot infogram from cross-validation hold out dataset
        :return: 
        """

        
        plt = get_matplotlib_pyplot(server, raise_if_not_available=True)
        
        rel_cmi_frame = self.get_relevance_cmi_frame(valid=valid, xval=xval)            
        if rel_cmi_frame is None:
            raise H2OValueError("Cannot locate the H2OFrame containing the infogram data.")
        
        rel_cmi_frame_names = rel_cmi_frame.names
        x_label = rel_cmi_frame_names[3]
        y_label = rel_cmi_frame_names[4]
        ig_x_column = 3
        ig_y_column = 4
        index_of_admissible = 1
        features_column = 0
        x_thresh = self.actual_params["relevance_threshold"]
        y_thresh = self.actual_params["cmi_threshold"]
        
        xmax=1.1
        ymax=1.1

        X = np.array(rel_cmi_frame[ig_x_column].as_data_frame(header=False, use_pandas=False)).astype(float).reshape((-1,))
        Y = np.array(rel_cmi_frame[ig_y_column].as_data_frame(header=False, use_pandas=False)).astype(float).reshape((-1,))
        features = np.array(rel_cmi_frame[features_column].as_data_frame(header=False, use_pandas=False)).reshape((-1,))
        admissible = np.array(rel_cmi_frame[index_of_admissible].as_data_frame(header=False, use_pandas=False)).astype(float).reshape((-1,))
        
        mask = admissible > 0
        
        plt.figure(figsize=figsize)
        plt.grid(True)
        plt.scatter(X, Y, zorder=10, c=np.where(mask, "black", "gray"))
        plt.hlines(y_thresh, xmin=x_thresh, xmax=xmax, colors="red", linestyle="dashed")
        plt.vlines(x_thresh, ymin=y_thresh, ymax=ymax, colors="red", linestyle="dashed")
        plt.gca().add_collection(PolyCollection(verts=[[(0,0), (0, ymax), (x_thresh, ymax), (x_thresh, y_thresh), (xmax, y_thresh), (xmax, 0)]],
                                                color="#CC663E", alpha=0.1, zorder=5))
        
        for i in mask.nonzero()[0]:
            plt.annotate(features[i], (X[i], Y[i]), xytext=(0, -10), textcoords="offset points",
                         horizontalalignment='center', verticalalignment='top', color="blue")
        
        plt.xlim(0, 1.05)
        plt.ylim(0, 1.05)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title("Infogram")
        fig = plt.gcf()
        if not server:
            plt.show()
        return fig
        
    def get_relevance_cmi_frame(self, valid=False, xval=False):
        """
        Get the relevance and CMI for all attributes returned by Infogram as an H2O Frame.
        :param self: 
        :return: H2OFrame
        """
        keyString = self._model_json["output"]["relevance_cmi_key"]
        if (valid):
            keyString = self._model_json["output"]["relevance_cmi_valid"]
        elif (xval):
            keyString = self._model_json["output"]["relevance_cmi_xval"]
            
        if keyString is None:
            return None
        else:
            return h2o.get_frame(keyString)

    def get_admissible_attributes(self):
        """
        Get the admissible attributes
        :param self: 
        :return: 
        """
        if self._model_json["output"]["admissible_features"] is None:
            return None
        else:
            return self._model_json["output"]["admissible_features"]

    def get_admissible_relevance(self):
        """
        Get the relevance of admissible attributes
        :param self: 
        :return: 
        """
        if self._model_json["output"]["admissible_relevance"] is None:
            return None
        else:
            return self._model_json["output"]["admissible_relevance"]

    def get_admissible_cmi(self):
        """
        Get the normalized cmi of admissible attributes
        :param self: 
        :return: 
        """
        if self._model_json["output"]["admissible_cmi"] is None:
            return None
        else:
            return self._model_json["output"]["admissible_cmi"]

    def get_admissible_cmi_raw(self):
        """
        Get the raw cmi of admissible attributes
        :param self: 
        :return: 
        """
        if self._model_json["output"]["admissible_cmi_raw"] is None:
            return None
        else:
            return self._model_json["output"]["admissible_cmi_raw"]

    def get_all_predictor_relevance(self):
        """
        Get relevance of all predictors
        :param self: 
        :return: two tuples, first one is predictor names and second one is relevance
        """
        if self._model_json["output"]["all_predictor_names"] is None:
            return None
        else:
            return self._model_json["output"]["all_predictor_names"], self._model_json["output"]["relevance"]

    def get_all_predictor_cmi(self):
        """
        Get normalized cmi of all predictors.
        :param self: 
        :return: two tuples, first one is predictor names and second one is cmi
        """
        if self._model_json["output"]["all_predictor_names"] is None:
            return None
        else:
            return self._model_json["output"]["all_predictor_names"], self._model_json["output"]["cmi"]

    def get_all_predictor_cmi_raw(self):
        """
        Get raw cmi of all predictors.
        :param self: 
        :return: two tuples, first one is predictor names and second one is cmi
        """
        if self._model_json["output"]["all_predictor_names"] is None:
            return None
        else:
            return self._model_json["output"]["all_predictor_names"], self._model_json["output"]["cmi_raw"]
        
    # Override train method to support infogram needs
    def train(self, x=None, y=None, training_frame=None, verbose=False, **kwargs):
        sup = super(self.__class__, self)
        
        def extend_parms(parms):  # add parameter checks specific to infogram
            if parms["data_fraction"] is not None:
                assert_is_type(parms["data_fraction"], numeric)
                assert parms["data_fraction"] > 0 and parms["data_fraction"] <= 1, "data_fraction should exceed 0" \
                                                                                   " and <= 1."
        
        parms = sup._make_parms(x,y,training_frame, extend_parms_fn = extend_parms, **kwargs)
        sup._train(parms, verbose=verbose)
        # can probably get rid of model attributes that Erin does not want here
        return self

extensions = dict(
    __imports__="""
import ast
import json
import warnings
import h2o
from h2o.utils.typechecks import assert_is_type, is_type, numeric
from h2o.frame import H2OFrame
import numpy as np
from h2o.utils.ext_dependencies import get_matplotlib_pyplot
from matplotlib.collections import PolyCollection
""",
    __class__=class_extensions
)
       
overrides = dict(
    infogram_algorithm_params=dict(
        getter="""
if self._parms.get("{sname}") != None:
    infogram_algorithm_params_dict =  ast.literal_eval(self._parms.get("{sname}"))
    for k in infogram_algorithm_params_dict:
        if len(infogram_algorithm_params_dict[k]) == 1: #single parameter
            infogram_algorithm_params_dict[k] = infogram_algorithm_params_dict[k][0]
    return infogram_algorithm_params_dict
else:
    return self._parms.get("{sname}")
""",
        setter="""
assert_is_type({pname}, None, {ptype})
if {pname} is not None and {pname} != "":
    for k in {pname}:
        if ("[" and "]") not in str(infogram_algorithm_params[k]):
            infogram_algorithm_params[k] = [infogram_algorithm_params[k]]
    self._parms["{sname}"] = str(json.dumps({pname}))
else:
    self._parms["{sname}"] = None
"""
    ),
    relevance_index_threshold=dict(
        setter="""
if relevance_index_threshold <= 4.940656458e-324: # not set
    if self._parms["protected_columns"] is not None:    # fair infogram
        self._parms["relevance_index_threshold"]=0.1
else: # it is set
    if self._parms["protected_columns"] is not None:    # fair infogram
        self._parms["relevance_index_threshold"] = relevance_index_threshold
    else: # core infogram should not have been set
        warnings.warn("Should not set relevance_index_threshold for core infogram runs.  Set total_information_threshold instead.  Using default of 0.1 if not set", RuntimeWarning)
"""
    ),
    safety_index_threshold=dict(
        setter="""
if safety_index_threshold <= 4.940656458e-324: # not set
    if self._parms["protected_columns"] is not None:
        self._parms["safety_index_threshold"]=0.1
else: # it is set
    if self._parms["protected_columns"] is not None: # fair infogram
        self._parms["safety_index_threshold"] = safety_index_threshold
    else: # core infogram should not have been set
        warnings.warn("Should not set safety_index_threshold for core infogram runs.  Set net_information_threshold instead.  Using default of 0.1 if not set", RuntimeWarning)
"""
    ),
    net_information_threshold=dict(
        setter="""
if net_information_threshold <= 4.940656458e-324: # not set
    if self._parms["protected_columns"] is None:
        self._parms["net_information_threshold"]=0.1
else:  # set
    if self._parms["protected_columns"] is not None: # fair infogram
        warnings.warn("Should not set net_information_threshold for fair infogram runs.  Set safety_index_threshold instead.  Using default of 0.1 if not set", RuntimeWarning)
    else:
        self._parms["net_information_threshold"]=net_information_threshold
"""
    ),
    total_information_threshold=dict(
        setter="""
if total_information_threshold <= 4.940656458e-324: # not set
    if self._parms["protected_columns"] is None:
        self._parms["total_information_threshold"] = 0.1
else:
    if self._parms["protected_columns"] is not None: # fair infogram
        warnings.warn("Should not set total_information_threshold for fair infogram runs.  Set relevance_index_threshold instead.  Using default of 0.1 if not set", RuntimeWarning)
    else:
        self._parms["total_information_threshold"] = total_information_threshold
"""
    )
)

doc = dict(
    __class__="""
Given a sensitive/unfair predictors list, Infogram will add all predictors that contains information on the 
 sensitive/unfair predictors list to the sensitive/unfair predictors list.  It will return a set of predictors that
 do not contain information on the sensitive/unfair list and hence user can build a fair model.  If no sensitive/unfair
 predictor list is given, Infogram will return a list of core predictors that should be used to build a final model.
 Infogram can significantly cut down the number of predictors needed to build a model and hence will build a simple
 model that is more interpretable, less susceptible to overfitting, runs faster while providing similar accuracy
 as models built using all attributes.
"""
)
