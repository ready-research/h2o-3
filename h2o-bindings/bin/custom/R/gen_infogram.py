rest_api_version = 3

def update_param(name, param):
    if name == 'model_algorithm_params':
        param['default_value'] = None
        return param
    elif name == 'infogram_algorithm_params':
        param['default_value'] = None
        return param
    return None  # param untouched

extensions = dict(
    required_params=['x', 'y', 'training_frame'],  # empty to override defaults in gen_defaults
    set_required_params="""
    parms$training_frame <- training_frame
    args <- .verify_dataxy(training_frame, x, y)
    if( !missing(offset_column) && !is.null(offset_column))  args$x_ignore <- args$x_ignore[!( offset_column == args$x_ignore )]
    if( !missing(weights_column) && !is.null(weights_column)) args$x_ignore <- args$x_ignore[!( weights_column == args$x_ignore )]
    if( !missing(fold_column) && !is.null(fold_column)) args$x_ignore <- args$x_ignore[!( fold_column == args$x_ignore )]
    parms$ignored_columns <- args$x_ignore
    parms$response_column <- args$y
    """,

    skip_default_set_params_for=['training_frame', 'ignored_columns', 'response_column', 'max_confusion_matrix_size',
                                 "interactions", "nfolds", "missing_values_handling", 
                                 "infogram_algorithm_params", "model_algorithm_params"],
    set_params="""
if (!missing(infogram_algorithm_params))
    parms$infogram_algorithm_params <- as.character(toJSON(infogram_algorithm_params, pretty = TRUE))
if (!missing(model_algorithm_params))
    parms$model_algorithm_params <- as.character(toJSON(model_algorithm_params, pretty = TRUE))
if( !missing(interactions) ) {
    # interactions are column names => as-is
    if( is.character(interactions) )       parms$interactions <- interactions
      else if( is.numeric(interactions) )    parms$interactions <- names(training_frame)[interactions]
      else stop(\"Don't know what to do with interactions. Supply vector of indices or names\")
}
    # For now, accept nfolds in the R interface if it is 0 or 1, since those values really mean do nothing.
    # For any other value, error out.
    # Expunge nfolds from the message sent to H2O, since H2O doesn't understand it.
if (!missing(nfolds) && nfolds > 1)
    parms$nfolds <- nfolds
if(!missing(missing_values_handling))
    parms$missing_values_handling <- missing_values_handling
""",
    with_model="""
# Convert infogram_algorithm_params back to list if not NULL
if (!missing(infogram_algorithm_params)) {
    model@parameters$infogram_algorithm_params <- list(fromJSON(model@parameters$infogram_algorithm_params))[[1]] #Need the `[[ ]]` to avoid a nested list
}
if (!missing(model_algorithm_params)) {
    model@parameters$model_algorithm_params <- list(fromJSON(model@parameters$model_algorithm_params))[[1]] #Need the `[[ ]]` to avoid a nested list
}
""",
    module="""
.h2o.get_relevance_cmi_frame<- function(model) {
  if( is(model, "H2OModel") ) {
  return(model)
  }
}
"""
)
# modify this for infogram.
doc = dict(
    preamble="""
Given a sensitive/unfair predictors list, InfoGram will add all predictors that contains information on the 
 sensitive/unfair predictors list to the sensitive/unfair predictors list.  It will return a set of predictors that
 do not contain information on the sensitive/unfair list and hence user can build a fair model.  If no sensitive/unfair
 predictor list is given, InfoGram will return a list of core predictors that should be used to build a final model.
 InfoGram can significantly cut down the number of predictors needed to build a model and hence will build a simple
 model that is more interpretable, less susceptible to overfitting, runs faster while providing similar accuracy
 as models built using all attributes.
    """,
    examples="""
    h2o.init()

    # Run infogram of CAPSULE ~ AGE + RACE + PSA + DCAPS
    prostate_path <- system.file("extdata", "prostate.csv", package = "h2o")
    prostate <- h2o.uploadFile(path = prostate_path)
    prostate$CAPSULE <- as.factor(prostate$CAPSULE)
    h2o.infogram(y = "CAPSULE", x = c("RACE", "AGE", "PSA", "DCAPS"), training_frame = prostate, family = "binomial")
    """
)
