from pycolonies import colonies_client

colonies, colonyname, colony_prvkey, executor_name, prvkey = colonies_client()

try:
    colonies.upload_file(colonyname, prvkey, filepath="./test.txt", label="/testlabel")
    print("File uploaded successfully.")
except Exception as e:
    print(e)

try:
    data = b"Sample byte data to upload"
    colonies.upload_data(colonyname, prvkey, filename="mydata", data=data, label="/testlabel_data")
    print("Data uploaded successfully.")
except Exception as e:
    print(e)

files = colonies.get_files("/testlabel", colonyname, prvkey)
file = colonies.get_file(colonyname, prvkey, label="/testlabel", filename="test.txt")

try:
    dst = colonies.download_file(colonyname, prvkey, dst="./testlabel", label="/testlabel", filename="test.txt")
    print(f"File downloaded to {dst} successfully.")
except Exception as e:
    print(e)
         
try:
    dst = colonies.download_file(colonyname, prvkey, dst="./testlabel_data", label="/testlabel_data", filename="mydata")
    print(f"Data downloaded to {dst} successfully.")
except Exception as e:
    print(e)
        
try:
    data = colonies.download_data(colonyname, prvkey, label="/testlabel_data", filename="mydata")
    data_str = data.decode('utf-8')
    print(data_str)
except Exception as e:
    print(e)

try:
    colonies.delete_file(colonyname, prvkey, label="/testlabel_data", filename="mydata")
except Exception as e:
    print(e)

try:
    colonies.delete_file(colonyname, prvkey, label="/testlabel", filename="test.txt")
except Exception as e:
    print(e)
