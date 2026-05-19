# Project Overview

This project investigates how urban resources are distributed across different areas of Greater Sydney using POI data, census information, and spatial analysis methods. The main focus of the project is to compare how well different SA2 regions are resourced and whether there are noticeable differences between highly urbanised and more suburban areas.

The project began with cleaning and preparing the raw datasets. Several preprocessing steps were applied, including standardising column names and text fields, handling missing values, reshaping the data structure, and preparing geographic boundary information for later analysis and mapping. These steps were necessary to make the datasets easier to work with and more consistent across different tasks.

After the cleaning stage, POI data from categories such as recreation, transport, education, and community facilities were analysed. A scoring workflow was then used to calculate a well-resourced score for each SA2 region based mainly on the concentration of POIs and related indicators.

Different visualisations were produced during the analysis process, including score maps, POI distribution maps, ranking charts, and comparisons between well-resourced scores and median income levels. These visualisations helped show how accessibility and resource concentration varied between different parts of Sydney.

Overall, the results suggest that resource distribution is not evenly balanced across Greater Sydney. Some highly urbanised regions achieved much higher accessibility scores, while several suburban areas received lower scores. However, the scoring system also has limitations because it mainly depends on POI counts and simplified calculations. Factors such as transport quality, travel distance, service capacity, and population demand were not fully included in the model.
