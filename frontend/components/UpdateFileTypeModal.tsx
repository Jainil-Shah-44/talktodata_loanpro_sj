import { useEffect, useState } from "react";
import { Modal, Button, TextInput } from "@mantine/core";
import apiClient from "@/src/api/client";
import { mappingService } from "@/src/api/mappingService";
import { CreatableSelect } from "./CreatableSelect";

type Props = {
  datasetId: string;
  currentFileType:string;
  opened: boolean;
  onClose: () => void;
  onUpdated?: () => void;

};

export default function UpdateFileTypeModal({ datasetId, opened, onClose, onUpdated,currentFileType }: Props) {
  const [fileType, setFileType] = useState("");
  const [loading, setLoading] = useState(false);
  
  const [fileTypesList,setFileTypeList] = useState<string[]>([]);
  
  useEffect(()=>{
    setFileType(currentFileType??"");
  },[currentFileType]);
  
  useEffect(() => {
      (async () => {
        const res = await mappingService.getFileType();
        if(res!=null && res!=undefined)
          setFileTypeList(res);
      })();
  }, []);

  const updateFileType = async () => {
    setLoading(true);
    try {
        const res = await apiClient.put<any>(`/datasets/${datasetId}/file-type`,{
            file_type: fileType,
        });
      onUpdated?.();
      onClose();
      return res.data;
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <Modal opened={opened} onClose={onClose} title="Update File Type">
      {/* <TextInput
        label="File Type"
        placeholder="e.g., csv, json, xlsx"
        value={fileType}
        onChange={(e) => setFileType(e.target.value)}
      /> */}

      <CreatableSelect
              label="FileType"
              required
              // data={["PDF", "Excel", "CSV"]}
              data={fileTypesList}
              value={fileType}
              onChange={setFileType}
            />
      <Button fullWidth mt="md" loading={loading} onClick={updateFileType}>
        Update
      </Button>
    </Modal>
  );
}
