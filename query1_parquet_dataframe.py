from pyspark.sql import SparkSession
from pyspark.sql.functions import year, month, col, format_string, to_timestamp, row_number
from pyspark.sql.window import Window

# Create SparkSession
spark = SparkSession.builder.appName("Parquet_Dataframe").getOrCreate()

# Clean cache before execution
spark.catalog.clearCache()

# Read the data from Parquet files
crime_data_2010_to_2019 = spark.read.parquet("/home/user/hadoop_data/Crime_Data_from_2010_2019.parquet")
crime_data_2020_to_present = spark.read.parquet("/home/user/hadoop_data/Crime_Data_from_2020_present.parquet")

# Concatenate the data
crime_data = crime_data_2010_to_2019.union(crime_data_2020_to_present)

# Convert the column "DATE OCC" to datetime
crime_data = crime_data.withColumn("DATE OCC", to_timestamp("DATE OCC", "MM/dd/yyyy hh:mm:ss a"))

# Group the data by year and month and calculate the number of crimes
crime_data = crime_data.withColumn("Year", year("DATE OCC")).withColumn("Month", month("DATE OCC"))
crime_counts = crime_data.groupBy("Year", "Month").count().withColumnRenamed("count", "Crime Total")

# Sort the data by the number of crimes for each year
windowSpec = Window.partitionBy("Year").orderBy(col("Crime Total").desc())
sorted_crime_counts = crime_counts.withColumn("Ranking", row_number().over(windowSpec))

# Select the three months with the highest number of crimes for each year
top_months_per_year = sorted_crime_counts.filter(col("Ranking") <= 3).orderBy("Year", "Ranking")

top_months_per_year = top_months_per_year.withColumn("Year", format_string("%-4s", col("Year")))
top_months_per_year = top_months_per_year.withColumn("Month", format_string("%-5s", col("Month")))
top_months_per_year = top_months_per_year.withColumn("Crime Total", format_string("%-11s", col("Crime Total")))
top_months_per_year = top_months_per_year.withColumn("Ranking", format_string("%-7s", col("Ranking")))

# Save the results to a CSV file
top_months_per_year.write.format('csv').option('header', 'true').option('delimiter', '|').mode('overwrite').save('hdfs:///home/user/query1_parquet_dataframe')

print("The 3 months with the highest number of recorded crimes in ascending order of the year and descending order of the number of records:\n")
top_months_per_year.show(n=60)

