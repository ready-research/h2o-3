setwd(normalizePath(dirname(R.utils::commandArgs(asValues = TRUE)$"f")))
source("../../../scripts/h2o-r-test-setup.R")
library(uplift)


test.uplift <- function() {
  ntrees <- 10
  mtries <- 6
  seed <- 42
  uplift_metrics <- c("KL", "ChiSquared", "Euclidean")
  set.seed(seed)

  # Test data preparation for each implementation
  train <- sim_pte(n = 2000, p = 6, rho = 0, sigma = sqrt(2), beta.den = 4)
  train$treat <- ifelse(train$treat == 1, 1, 0)
  test <- sim_pte(n = 1000, p = 6, rho = 0, sigma = sqrt(2), beta.den = 4)
  test$treat <- ifelse(test$treat == 1, 1, 0)

  trainh2o <- train
  trainh2o$treat <- as.factor(train$treat)
  trainh2o$y <- as.factor(train$y)
  trainh2o <- as.h2o(trainh2o)

  testh2o <- test
  testh2o$treat <- as.factor(test$treat)
  testh2o$y <- as.factor(test$y)
  testh2o <- as.h2o(testh2o)
  
  expected_values_auuc_qini <- c(66.108996, 85.583648, 60.837472)
  expected_values_auuc_lift <- c(0.212531, 0.260563, 0.204788)
  expected_values_auuc_gain <- c(128.642298, 162.020112, 122.031586) 

  expected_values_aecu_qini <- c(82.12082, 101.594370, 76.857630)
  expected_values_aecu_lift <- c(0.2285426, 0.276573, 0.220808)
  expected_values_aecu_gain <- c(160.666, 194.041557, 154.071902)
    
  expected_values_auuc_norm_qini <- c(2.065906, 2.674489, 1.901171)
  expected_values_auuc_norm_gain <- c(2.010036, 2.531564, 1.906744)
  expected_values_auuc_norm_lift <- c(0.212531, 0.260563, 0.204788)
    
  for (i in 1:length(uplift_metrics)) {
    print(paste("Train h2o uplift model", uplift_metrics[i]))
    model <- h2o.upliftRandomForest(
        x = c("X1", "X2", "X3", "X4", "X5", "X6"),
        y = "y",
        training_frame = trainh2o,
        validation_frame = testh2o,
        treatment_column = "treat",
        uplift_metric = uplift_metrics[i],
        auuc_type = "qini",
        distribution = "bernoulli",
        ntrees = ntrees,
        mtries = mtries,
        max_depth = 10,
        min_rows = 10,
        nbins = 100,
        seed = seed) 
      
    print(model)  
        
    # test model metrics
    print("Test model metrics")
    auuc <- h2o.auuc(model, train=TRUE, valid=TRUE)
    print(auuc) 
    qini <- h2o.qini(model, train=TRUE, valid=TRUE)
    print(qini)
    aecu <- h2o.aecu(model, train=TRUE, valid=TRUE)
    print(aecu)
    auuc_normalized <- h2o.auuc_normalized(model, train=TRUE, valid=TRUE)
    print(auuc_normalized)  
       
    # test performance 
    print("Test performance metrics")
    perf <- h2o.performance(model)
    auuc <- h2o.auuc(perf)  
    print(auuc)
    auuc_qini <- h2o.auuc(perf, metric="qini")
    print(auuc_qini)
    auuc_gain <- h2o.auuc(perf, metric="gain")
    print(auuc_gain)
    auuc_lift <- h2o.auuc(perf, metric="lift")
    print(auuc_lift)
      
    auuc_table <- h2o.auuc_table(perf)
    print(auuc_table)
      
    qini <- h2o.qini(perf)
    print(qini)
      
    aecu_qini <- h2o.aecu(perf, metric="qini")
    print(aecu_qini)
    aecu_gain <- h2o.aecu(perf, metric="gain")
    print(aecu_gain)
    aecu_lift <- h2o.aecu(perf, metric="lift")
    print(aecu_lift)
      
    aecu_table <- h2o.aecu_table(perf)
    print(aecu_table)
    print(h2o.thresholds_and_metric_scores(perf))

    auuc_norm <- h2o.auuc_normalized(perf)
    print(auuc_norm)
    auuc_qini_norm <- h2o.auuc_normalized(perf, metric="qini")
    print(auuc_qini_norm)
    auuc_gain_norm <- h2o.auuc_normalized(perf, metric="gain")
    print(auuc_gain_norm)
    auuc_lift_norm <- h2o.auuc_normalized(perf, metric="lift")
    print(auuc_lift_norm)
      
    tol <- 1e-4
    expect_equal(auuc, auuc_qini, tolerance=tol)
    expect_equal(auuc, expected_values_auuc_qini[i], tolerance=tol)
    expect_equal(auuc_gain, expected_values_auuc_gain[i], tolerance=tol)
    expect_equal(auuc_lift, expected_values_auuc_lift[i], tolerance=tol)   
    expect_equal(qini, aecu_qini, tolerance=tol) 
    expect_equal(aecu_qini, expected_values_aecu_qini[i], tolerance=tol) 
    expect_equal(aecu_gain, expected_values_aecu_gain[i], tolerance=tol) 
    expect_equal(aecu_lift, expected_values_aecu_lift[i], tolerance=tol)

    expect_equal(auuc_norm, auuc_qini_norm, tolerance=tol)
    expect_equal(auuc_norm, expected_values_auuc_norm_qini[i], tolerance=tol)
    expect_equal(auuc_gain_norm, expected_values_auuc_norm_gain[i], tolerance=tol)
    expect_equal(auuc_lift_norm, expected_values_auuc_norm_lift[i], tolerance=tol)
      
    model_ate <- h2o.ate(model, train=TRUE, valid=TRUE)
    print(model_ate)
    perf_ate <- h2o.ate(perf)
    print(perf_ate)
    expect_equal(model_ate[["train"]], perf_ate, tolerance=tol)
      
    model_att <- h2o.att(model, train=TRUE, valid=TRUE)
    print(model_att)  
    perf_att <- h2o.att(perf)
    print(perf_att)
    expect_equal(model_att[["train"]], perf_att, tolerance=tol)

    model_atc <- h2o.atc(model, train=TRUE, valid=TRUE)
    print(model_atc)  
    perf_atc <- h2o.atc(perf)
    print(perf_atc)
    expect_equal(model_atc[["train"]], perf_atc, tolerance=tol)

    plot(perf)
    plot(perf, normalize=TRUE)  
  }
}

doTest("Uplift Random Forest Test: Test H2O RF uplift", test.uplift)
