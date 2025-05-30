{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyNxq+4zql8xueBQjsVHyKcB",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/ivanliu33178/Hello-World/blob/master/Pig-ai_model.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "# --- Step 1: Upload your Google Sheets API JSON key ---\n",
        "from google.colab import files\n",
        "uploaded = files.upload()  # Upload your JSON key file here\n",
        "\n",
        "# --- Step 2: Install necessary libraries ---\n",
        "!pip install --upgrade gspread gspread-dataframe xgboost scikit-learn pandas\n",
        "\n",
        "# --- Step 3: Imports and authorize ---\n",
        "import gspread\n",
        "from oauth2client.service_account import ServiceAccountCredentials\n",
        "import pandas as pd\n",
        "from gspread_dataframe import get_as_dataframe, set_with_dataframe\n",
        "\n",
        "# Use uploaded JSON key filename automatically\n",
        "json_file = list(uploaded.keys())[0]\n",
        "\n",
        "# Define scope and authorize client\n",
        "scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']\n",
        "creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)\n",
        "client = gspread.authorize(creds)\n",
        "\n",
        "# --- Step 4: Open Google Sheet and worksheet ---\n",
        "spreadsheet = client.open(\"A4/B4 Daily record\")   # <-- Change to your sheet name\n",
        "worksheet = spreadsheet.worksheet(\"P-1\")            # <-- Change to your worksheet/tab name\n",
        "\n",
        "# --- Step 5: Load data into pandas DataFrame ---\n",
        "df = get_as_dataframe(worksheet)\n",
        "df = df.dropna(how='all')  # drop empty rows\n",
        "\n",
        "# --- Step 6: Preprocess data ---\n",
        "# Rename columns to English for convenience\n",
        "df.rename(columns={\n",
        "    'Batch no.': 'BatchNo',\n",
        "    'ရက်စွဲ': 'Date',\n",
        "    'Est_Feed_intake_Kg': 'FeedIntake',\n",
        "    'အစာနံပါတ်': 'FeedID'\n",
        "}, inplace=True)\n",
        "\n",
        "df['Date'] = pd.to_datetime(df['Date'], errors='coerce')\n",
        "df.dropna(subset=['FeedIntake', 'BatchNo', 'Date', 'FeedID'], inplace=True)\n",
        "\n",
        "# Extract date features\n",
        "df['day_of_week'] = df['Date'].dt.dayofweek\n",
        "df['month'] = df['Date'].dt.month\n",
        "\n",
        "# --- Step 7: Prepare features and target ---\n",
        "from sklearn.model_selection import train_test_split\n",
        "from sklearn.linear_model import LinearRegression\n",
        "from sklearn.metrics import r2_score\n",
        "import xgboost as xgb\n",
        "\n",
        "X = df[['BatchNo', 'FeedID', 'day_of_week', 'month']]\n",
        "y = df['FeedIntake']\n",
        "\n",
        "# One-hot encode categorical if any\n",
        "X = pd.get_dummies(X)\n",
        "\n",
        "# Train/test split\n",
        "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n",
        "\n",
        "# --- Step 8: Train models ---\n",
        "# Linear Regression\n",
        "lr_model = LinearRegression()\n",
        "lr_model.fit(X_train, y_train)\n",
        "lr_preds = lr_model.predict(X_test)\n",
        "print(\"📊 Linear Regression R²:\", r2_score(y_test, lr_preds))\n",
        "\n",
        "# XGBoost\n",
        "xgb_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)\n",
        "xgb_model.fit(X_train, y_train)\n",
        "xgb_preds = xgb_model.predict(X_test)\n",
        "print(\"📊 XGBoost R²:\", r2_score(y_test, xgb_preds))\n",
        "\n",
        "# --- Step 9: Predict for all data and write back to new sheet ---\n",
        "df_full = df.copy()\n",
        "X_full = df_full[['BatchNo', 'FeedID', 'day_of_week', 'month']]\n",
        "X_full = pd.get_dummies(X_full)\n",
        "\n",
        "# Align columns with training features (in case some dummy columns are missing)\n",
        "X_full = X_full.reindex(columns=X.columns, fill_value=0)\n",
        "\n",
        "# Predict feed intake\n",
        "df_full['Predicted_FeedIntake'] = xgb_model.predict(X_full)\n",
        "\n",
        "# Create or open a new worksheet \"AItesting\"\n",
        "try:\n",
        "    new_worksheet = spreadsheet.worksheet(\"AItesting\")\n",
        "except gspread.exceptions.WorksheetNotFound:\n",
        "    new_worksheet = spreadsheet.add_worksheet(\n",
        "        title=\"AItesting\",\n",
        "        rows=str(len(df_full) + 10),\n",
        "        cols=str(len(df_full.columns) + 5)\n",
        "    )\n",
        "\n",
        "# Write the dataframe with predictions to the new sheet\n",
        "set_with_dataframe(new_worksheet, df_full)\n",
        "\n",
        "print(\"✅ Predictions successfully written to new sheet 'AItesting'.\")\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/",
          "height": 648
        },
        "id": "U9d95u5VXqm9",
        "outputId": "ffb7caab-b07e-4668-de6d-9f6677634b64"
      },
      "execution_count": 12,
      "outputs": [
        {
          "output_type": "display_data",
          "data": {
            "text/plain": [
              "<IPython.core.display.HTML object>"
            ],
            "text/html": [
              "\n",
              "     <input type=\"file\" id=\"files-f756ca73-f381-47fc-9a9b-cde3ead4ab04\" name=\"files[]\" multiple disabled\n",
              "        style=\"border:none\" />\n",
              "     <output id=\"result-f756ca73-f381-47fc-9a9b-cde3ead4ab04\">\n",
              "      Upload widget is only available when the cell has been executed in the\n",
              "      current browser session. Please rerun this cell to enable.\n",
              "      </output>\n",
              "      <script>// Copyright 2017 Google LLC\n",
              "//\n",
              "// Licensed under the Apache License, Version 2.0 (the \"License\");\n",
              "// you may not use this file except in compliance with the License.\n",
              "// You may obtain a copy of the License at\n",
              "//\n",
              "//      http://www.apache.org/licenses/LICENSE-2.0\n",
              "//\n",
              "// Unless required by applicable law or agreed to in writing, software\n",
              "// distributed under the License is distributed on an \"AS IS\" BASIS,\n",
              "// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n",
              "// See the License for the specific language governing permissions and\n",
              "// limitations under the License.\n",
              "\n",
              "/**\n",
              " * @fileoverview Helpers for google.colab Python module.\n",
              " */\n",
              "(function(scope) {\n",
              "function span(text, styleAttributes = {}) {\n",
              "  const element = document.createElement('span');\n",
              "  element.textContent = text;\n",
              "  for (const key of Object.keys(styleAttributes)) {\n",
              "    element.style[key] = styleAttributes[key];\n",
              "  }\n",
              "  return element;\n",
              "}\n",
              "\n",
              "// Max number of bytes which will be uploaded at a time.\n",
              "const MAX_PAYLOAD_SIZE = 100 * 1024;\n",
              "\n",
              "function _uploadFiles(inputId, outputId) {\n",
              "  const steps = uploadFilesStep(inputId, outputId);\n",
              "  const outputElement = document.getElementById(outputId);\n",
              "  // Cache steps on the outputElement to make it available for the next call\n",
              "  // to uploadFilesContinue from Python.\n",
              "  outputElement.steps = steps;\n",
              "\n",
              "  return _uploadFilesContinue(outputId);\n",
              "}\n",
              "\n",
              "// This is roughly an async generator (not supported in the browser yet),\n",
              "// where there are multiple asynchronous steps and the Python side is going\n",
              "// to poll for completion of each step.\n",
              "// This uses a Promise to block the python side on completion of each step,\n",
              "// then passes the result of the previous step as the input to the next step.\n",
              "function _uploadFilesContinue(outputId) {\n",
              "  const outputElement = document.getElementById(outputId);\n",
              "  const steps = outputElement.steps;\n",
              "\n",
              "  const next = steps.next(outputElement.lastPromiseValue);\n",
              "  return Promise.resolve(next.value.promise).then((value) => {\n",
              "    // Cache the last promise value to make it available to the next\n",
              "    // step of the generator.\n",
              "    outputElement.lastPromiseValue = value;\n",
              "    return next.value.response;\n",
              "  });\n",
              "}\n",
              "\n",
              "/**\n",
              " * Generator function which is called between each async step of the upload\n",
              " * process.\n",
              " * @param {string} inputId Element ID of the input file picker element.\n",
              " * @param {string} outputId Element ID of the output display.\n",
              " * @return {!Iterable<!Object>} Iterable of next steps.\n",
              " */\n",
              "function* uploadFilesStep(inputId, outputId) {\n",
              "  const inputElement = document.getElementById(inputId);\n",
              "  inputElement.disabled = false;\n",
              "\n",
              "  const outputElement = document.getElementById(outputId);\n",
              "  outputElement.innerHTML = '';\n",
              "\n",
              "  const pickedPromise = new Promise((resolve) => {\n",
              "    inputElement.addEventListener('change', (e) => {\n",
              "      resolve(e.target.files);\n",
              "    });\n",
              "  });\n",
              "\n",
              "  const cancel = document.createElement('button');\n",
              "  inputElement.parentElement.appendChild(cancel);\n",
              "  cancel.textContent = 'Cancel upload';\n",
              "  const cancelPromise = new Promise((resolve) => {\n",
              "    cancel.onclick = () => {\n",
              "      resolve(null);\n",
              "    };\n",
              "  });\n",
              "\n",
              "  // Wait for the user to pick the files.\n",
              "  const files = yield {\n",
              "    promise: Promise.race([pickedPromise, cancelPromise]),\n",
              "    response: {\n",
              "      action: 'starting',\n",
              "    }\n",
              "  };\n",
              "\n",
              "  cancel.remove();\n",
              "\n",
              "  // Disable the input element since further picks are not allowed.\n",
              "  inputElement.disabled = true;\n",
              "\n",
              "  if (!files) {\n",
              "    return {\n",
              "      response: {\n",
              "        action: 'complete',\n",
              "      }\n",
              "    };\n",
              "  }\n",
              "\n",
              "  for (const file of files) {\n",
              "    const li = document.createElement('li');\n",
              "    li.append(span(file.name, {fontWeight: 'bold'}));\n",
              "    li.append(span(\n",
              "        `(${file.type || 'n/a'}) - ${file.size} bytes, ` +\n",
              "        `last modified: ${\n",
              "            file.lastModifiedDate ? file.lastModifiedDate.toLocaleDateString() :\n",
              "                                    'n/a'} - `));\n",
              "    const percent = span('0% done');\n",
              "    li.appendChild(percent);\n",
              "\n",
              "    outputElement.appendChild(li);\n",
              "\n",
              "    const fileDataPromise = new Promise((resolve) => {\n",
              "      const reader = new FileReader();\n",
              "      reader.onload = (e) => {\n",
              "        resolve(e.target.result);\n",
              "      };\n",
              "      reader.readAsArrayBuffer(file);\n",
              "    });\n",
              "    // Wait for the data to be ready.\n",
              "    let fileData = yield {\n",
              "      promise: fileDataPromise,\n",
              "      response: {\n",
              "        action: 'continue',\n",
              "      }\n",
              "    };\n",
              "\n",
              "    // Use a chunked sending to avoid message size limits. See b/62115660.\n",
              "    let position = 0;\n",
              "    do {\n",
              "      const length = Math.min(fileData.byteLength - position, MAX_PAYLOAD_SIZE);\n",
              "      const chunk = new Uint8Array(fileData, position, length);\n",
              "      position += length;\n",
              "\n",
              "      const base64 = btoa(String.fromCharCode.apply(null, chunk));\n",
              "      yield {\n",
              "        response: {\n",
              "          action: 'append',\n",
              "          file: file.name,\n",
              "          data: base64,\n",
              "        },\n",
              "      };\n",
              "\n",
              "      let percentDone = fileData.byteLength === 0 ?\n",
              "          100 :\n",
              "          Math.round((position / fileData.byteLength) * 100);\n",
              "      percent.textContent = `${percentDone}% done`;\n",
              "\n",
              "    } while (position < fileData.byteLength);\n",
              "  }\n",
              "\n",
              "  // All done.\n",
              "  yield {\n",
              "    response: {\n",
              "      action: 'complete',\n",
              "    }\n",
              "  };\n",
              "}\n",
              "\n",
              "scope.google = scope.google || {};\n",
              "scope.google.colab = scope.google.colab || {};\n",
              "scope.google.colab._files = {\n",
              "  _uploadFiles,\n",
              "  _uploadFilesContinue,\n",
              "};\n",
              "})(self);\n",
              "</script> "
            ]
          },
          "metadata": {}
        },
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "Saving carbide-ward-261820-fc3304e67379.json to carbide-ward-261820-fc3304e67379 (5).json\n",
            "Requirement already satisfied: gspread in /usr/local/lib/python3.11/dist-packages (6.2.1)\n",
            "Requirement already satisfied: gspread-dataframe in /usr/local/lib/python3.11/dist-packages (4.0.0)\n",
            "Requirement already satisfied: xgboost in /usr/local/lib/python3.11/dist-packages (3.0.2)\n",
            "Requirement already satisfied: scikit-learn in /usr/local/lib/python3.11/dist-packages (1.6.1)\n",
            "Requirement already satisfied: pandas in /usr/local/lib/python3.11/dist-packages (2.2.3)\n",
            "Requirement already satisfied: google-auth>=1.12.0 in /usr/local/lib/python3.11/dist-packages (from gspread) (2.38.0)\n",
            "Requirement already satisfied: google-auth-oauthlib>=0.4.1 in /usr/local/lib/python3.11/dist-packages (from gspread) (1.2.2)\n",
            "Requirement already satisfied: six>=1.12.0 in /usr/local/lib/python3.11/dist-packages (from gspread-dataframe) (1.17.0)\n",
            "Requirement already satisfied: numpy in /usr/local/lib/python3.11/dist-packages (from xgboost) (2.0.2)\n",
            "Requirement already satisfied: nvidia-nccl-cu12 in /usr/local/lib/python3.11/dist-packages (from xgboost) (2.21.5)\n",
            "Requirement already satisfied: scipy in /usr/local/lib/python3.11/dist-packages (from xgboost) (1.15.3)\n",
            "Requirement already satisfied: joblib>=1.2.0 in /usr/local/lib/python3.11/dist-packages (from scikit-learn) (1.5.0)\n",
            "Requirement already satisfied: threadpoolctl>=3.1.0 in /usr/local/lib/python3.11/dist-packages (from scikit-learn) (3.6.0)\n",
            "Requirement already satisfied: python-dateutil>=2.8.2 in /usr/local/lib/python3.11/dist-packages (from pandas) (2.9.0.post0)\n",
            "Requirement already satisfied: pytz>=2020.1 in /usr/local/lib/python3.11/dist-packages (from pandas) (2025.2)\n",
            "Requirement already satisfied: tzdata>=2022.7 in /usr/local/lib/python3.11/dist-packages (from pandas) (2025.2)\n",
            "Requirement already satisfied: cachetools<6.0,>=2.0.0 in /usr/local/lib/python3.11/dist-packages (from google-auth>=1.12.0->gspread) (5.5.2)\n",
            "Requirement already satisfied: pyasn1-modules>=0.2.1 in /usr/local/lib/python3.11/dist-packages (from google-auth>=1.12.0->gspread) (0.4.2)\n",
            "Requirement already satisfied: rsa<5,>=3.1.4 in /usr/local/lib/python3.11/dist-packages (from google-auth>=1.12.0->gspread) (4.9.1)\n",
            "Requirement already satisfied: requests-oauthlib>=0.7.0 in /usr/local/lib/python3.11/dist-packages (from google-auth-oauthlib>=0.4.1->gspread) (2.0.0)\n",
            "Requirement already satisfied: pyasn1<0.7.0,>=0.6.1 in /usr/local/lib/python3.11/dist-packages (from pyasn1-modules>=0.2.1->google-auth>=1.12.0->gspread) (0.6.1)\n",
            "Requirement already satisfied: oauthlib>=3.0.0 in /usr/local/lib/python3.11/dist-packages (from requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (3.2.2)\n",
            "Requirement already satisfied: requests>=2.0.0 in /usr/local/lib/python3.11/dist-packages (from requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (2.32.3)\n",
            "Requirement already satisfied: charset-normalizer<4,>=2 in /usr/local/lib/python3.11/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (3.4.2)\n",
            "Requirement already satisfied: idna<4,>=2.5 in /usr/local/lib/python3.11/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (3.10)\n",
            "Requirement already satisfied: urllib3<3,>=1.21.1 in /usr/local/lib/python3.11/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (2.4.0)\n",
            "Requirement already satisfied: certifi>=2017.4.17 in /usr/local/lib/python3.11/dist-packages (from requests>=2.0.0->requests-oauthlib>=0.7.0->google-auth-oauthlib>=0.4.1->gspread) (2025.4.26)\n"
          ]
        },
        {
          "output_type": "stream",
          "name": "stderr",
          "text": [
            "<ipython-input-12-925a345720a2>:39: UserWarning: Parsing dates in %d/%m/%Y format when dayfirst=False (the default) was specified. Pass `dayfirst=True` or specify a format to silence this warning.\n",
            "  df['Date'] = pd.to_datetime(df['Date'], errors='coerce')\n"
          ]
        },
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "📊 Linear Regression R²: 0.5309297483783159\n",
            "📊 XGBoost R²: 0.6716549927098538\n",
            "✅ Predictions successfully written to new sheet 'AItesting'.\n"
          ]
        }
      ]
    }
  ]
}