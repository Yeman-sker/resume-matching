import unittest

from pyspark.sql import Row, SparkSession

from batch_processing.batch_job import (
    InsufficientTrainingData,
    calculate_scores,
    entity_struct,
    fit_feature_models,
    prepare_input_data,
)


class BatchJobTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = (
            SparkSession.builder.master("local[1]")
            .appName("BatchJobTest")
            .config("spark.ui.enabled", "false")
            .config("spark.sql.shuffle.partitions", "1")
            .getOrCreate()
        )
        cls.spark.sparkContext.setLogLevel("ERROR")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_calculate_scores_returns_rule_score_and_uses_60_40_total(self):
        resume = Row(
            standard_skills_array=["Python", "SQL"],
            education_level=3,
            experience_years_num=2,
            standard_location="南昌",
            expected_salary=10,
            certification_items_array=["英语四级"],
        )
        job = Row(
            required_skills_standard_array=["Python", "Spark"],
            preferred_skills_standard_array=["SQL"],
            education_required_level=3,
            experience_required_num=2,
            standard_location="南昌",
            salary_max=12,
        )

        scores = calculate_scores(resume, job, 80.0, 60.0)

        expected_semantic = 80.0 * 0.6 + 60.0 * 0.4
        expected_rule = (
            scores["skill_score"] * 0.40
            + scores["education_score"] * 0.20
            + scores["experience_score"] * 0.15
            + scores["city_score"] * 0.10
            + scores["salary_score"] * 0.10
            + scores["certificate_score"] * 0.05
        )
        self.assertAlmostEqual(scores["semantic_score"], expected_semantic)
        self.assertAlmostEqual(scores["rule_score"], expected_rule)
        self.assertAlmostEqual(
            scores["total_score"], expected_semantic * 0.60 + expected_rule * 0.40
        )

    def test_prepare_input_data_keeps_empty_tokens_transformable(self):
        resumes = self.spark.createDataFrame(
            [
                (
                    "RES_1",
                    None,
                    None,
                    None,
                )
            ],
            "resume_id string, tokens string, standard_skills string, "
            "certification_items string",
        )
        jobs = self.spark.createDataFrame(
            [
                (
                    "JOB_1",
                    "[]",
                    None,
                    None,
                )
            ],
            "job_id string, tokens string, required_skills_standard string, "
            "preferred_skills_standard string",
        )

        prepared_resumes, prepared_jobs = prepare_input_data(resumes, jobs)

        self.assertEqual(prepared_resumes.first().tokens, [])
        self.assertEqual(prepared_jobs.first().tokens, [])

        train_df = self.spark.createDataFrame(
            [(["Python"],), (["Python", "Spark"],)],
            "tokens array<string>",
        )
        _, _, w2v_model = fit_feature_models(train_df)
        self.assertEqual(
            len(w2v_model.transform(prepared_resumes).first().w2v_vector),
            100,
        )

    def test_entity_struct_restores_original_field_names(self):
        dataframe = self.spark.createDataFrame(
            [("RES_1", ["Python"])],
            "resume_id string, tokens array<string>",
        )
        columns = dataframe.columns
        renamed = dataframe.select(
            [dataframe[name].alias(f"resume_{name}") for name in columns]
        )

        entity = renamed.select(
            entity_struct("resume", columns).alias("resume")
        ).first().resume

        self.assertEqual(entity.resume_id, "RES_1")
        self.assertEqual(entity.tokens, ["Python"])

    def test_fit_feature_models_rejects_empty_vocabulary(self):
        train_df = self.spark.createDataFrame(
            [(["Python"],), (["Spark"],)], "tokens array<string>"
        )

        with self.assertRaises(InsufficientTrainingData):
            fit_feature_models(train_df)


if __name__ == "__main__":
    unittest.main()
