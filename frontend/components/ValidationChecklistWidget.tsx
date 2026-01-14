import { useEffect, useState } from 'react';
import { Table, Button, Modal, Loader, Text, ScrollArea } from '@mantine/core';
import { validationService } from '@/src/api/services';
//Added by jainil, merged hvb @ 15/12/2025
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import type { CSSProperties } from "react";

interface ValidationChecklistWidgetProps {
  datasetId: string;
}

interface ValidationRule {
  id: string;
  name: string;
  failed_count: number;
}



const stickyHeaderStyle: CSSProperties = {
  position: "sticky",
  top: 0, 
  zIndex: 5,
  background: "#fff",
  boxShadow: "0 2px 4px rgba(0,0,0,0.08)",
};

const stickyFirstColumnHeaderStyle: CSSProperties = {
  position: "sticky",
  top: 0,
  left: 0,
  zIndex: 6, // highest
  background: "#fff",
  boxShadow: "2px 0 4px rgba(0,0,0,0.1)",
};

const stickyCellStyle: CSSProperties = {
  position: "sticky",
  left: 0,
  zIndex: 3,
  background: "#fff",
  boxShadow: "2px 0 4px rgba(0,0,0,0.05)",
};



export function ValidationChecklistWidget({ datasetId }: ValidationChecklistWidgetProps) {
  const [validations, setValidations] = useState<ValidationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedValidation, setSelectedValidation] = useState<ValidationRule | null>(null);
  const [failedRecords, setFailedRecords] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [recordsLoading, setRecordsLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    validationService.getValidations(datasetId).then((data) => {
      setValidations(data);
      setLoading(false);
    });
  }, [datasetId]);

  const handleViewDetails = async (validation: ValidationRule) => {
    setSelectedValidation(validation);
    setModalOpen(true);
    setRecordsLoading(true);
    try {
      const records = await validationService.getValidationErrors(datasetId, validation.id);
      setFailedRecords(records);
    } catch (e) {
      setFailedRecords([]);
    }
    setRecordsLoading(false);
  };
  
//Added by jainil, merged hvb @ 15/12/2025
const handleExportExcel = () => {
  if (failedRecords.length === 0) return;

  // Convert failedRecords array into Excel worksheet
  const worksheet = XLSX.utils.json_to_sheet(failedRecords);

  // Create a workbook
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Failed Records");

  // Generate excel buffer
  const excelBuffer = XLSX.write(workbook, {
    bookType: "xlsx",
    type: "array",
  });

  // Convert to Blob and trigger download
  const blob = new Blob([excelBuffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });

  saveAs(blob, `${selectedValidation?.name || "validation"}_failed_records.xlsx`);
};


  if (loading) return <Loader />;

  return (
    <>
      <Table withTableBorder withColumnBorders mb="lg">
        <thead>
          <tr>
            <th>Validation</th>
            <th>Errors</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {validations.map((v) => (
            <tr key={v.id}>
              <td>{v.name}</td>
              <td>{v.failed_count}</td>
              <td>
                <Button
                  size="xs"
                  onClick={() => handleViewDetails(v)}
                  disabled={v.failed_count === 0}
                >
                  View Details
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
      <Modal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        title={selectedValidation?.name}
        size="90%"
      >
        {recordsLoading ? (
          <Loader />
        ) : failedRecords.length === 0 ? (
          <Text>No failed records.</Text>
        ) : (
          <>
            <Button mb="md" onClick={handleExportExcel}>
              Export to Excel
            </Button>

            {/* Horizontal + Vertical Scroll */}
            <ScrollArea
                type="auto"
                offsetScrollbars
                scrollbarSize={8}
                style={{
                      height: "60vh",        // KEY FIX
                      maxHeight: "60vh",
                    }}
              >
                <Table
                  withTableBorder
                  withColumnBorders
                  style={{
                    width: "100%",
                    minWidth: "max-content",
                  }}
                >
                  <thead>
                    <tr>
                      {Object.keys(failedRecords[0]).map((col, colIndex) => (
                        <th
                            key={col}
                            style={{
                              padding: "8px",
                              whiteSpace: "nowrap",
                              ...(colIndex === 0
                                ? stickyFirstColumnHeaderStyle // sticky corner
                                : stickyHeaderStyle),               // sticky header
                            }}
                          >
                            {col}
                          </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {failedRecords.map((rec, rowIndex) => (
                      <tr key={rowIndex}>
                        {Object.keys(failedRecords[0]).map((col, colIndex) => (
                          <td
                            key={col}
                            style={{
                              padding: "6px 8px",
                              whiteSpace: "nowrap",
                              ...(colIndex === 0 ? stickyCellStyle : {}),
                            }}
                          >
                            {rec[col] !== null && rec[col] !== undefined
                              ? String(rec[col])
                              : "-"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ScrollArea>

          </>
        )}
      </Modal>

    </>
  );
} 