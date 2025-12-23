import { useState, useEffect } from 'react';
import { Modal, Button, Group, Text, Stack, TextInput, Select, NumberInput, Checkbox, CloseButton, Box } from '@mantine/core';
import { IconPlus, IconTrash, IconCheck, IconX } from '@tabler/icons-react';
import { FitlerSaveActions } from '@/components/FilterSaveActions';
import { FilterCriteria } from '@/src/types/index';

//Added hvb @ 28/10/2025 for using filter management
import { filterManagementServices } from '@/src/api/services';
import { ColumnInfo } from '@/src/types/mappings';
import { useFieldState } from '@/hooks/useFieldState';
import FilterValuesDropdown from './FilterValuesDropdown';
import { VirtualizedSearchableSelect } from './VirtualizedSearchableSelect';

// shifted to types>index.ts hvb @ 27/10/2025
/*export interface FilterCriteria {
  field: string;
  operator: string;
  value?: number | string | null;
  min_value?: number | null;
  max_value?: number | null;
  enabled: boolean;
}*/

export interface PoolSelectionTarget {
  maxPoolValue: number;
  sortField: string;
  sortDirection: 'asc' | 'desc';
  sumValueField: string;
}

interface FilterCriteriaModalProps {
  opened: boolean;
  onClose: () => void;
  onApply: (filters: FilterCriteria[], target: PoolSelectionTarget) => void;
  //Mod hvb @ 10/12/2025
  //availableFields: { value: string; label: string }[];
  availableFields: ColumnInfo[];
  //This is supposed to be handled in popup and not the page who is calling this popup.
  //Shifted inside popup
  savedFilters?: { id: string; name: string; criteria: FilterCriteria[] }[];
  onSaveFilter?: (name: string, criteria: FilterCriteria[]) => void;
  initialFilters?: FilterCriteria[];
  initialTarget?: PoolSelectionTarget;
  datasetId:string|null
}

export function FilterCriteriaModal({
  opened,
  onClose,
  onApply,
  availableFields,
  savedFilters = [],
  onSaveFilter,
  //Mod hvb @ 12/12/2025 this are supposed to be pulled from db
  //initialFilters = [{ field: 'collection_12m', operator: '>=', value: 5000, enabled: true }],
  initialFilters = [],
  initialTarget = { maxPoolValue: 2500000, sortField: 'collection_12m', sortDirection: 'desc', sumValueField: 'principal_os_amt' },
  datasetId
}: FilterCriteriaModalProps) 
{
  const [filters, setFilters] = useState<FilterCriteria[]>(initialFilters);
  const [target, setTarget] = useState<PoolSelectionTarget>(initialTarget);
  const [selectedSavedFilter, setSelectedSavedFilter] = useState<string | null>(null);
  const [newFilterName, setNewFilterName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isFiltersLoading,setFilterLoading] = useState(false);

  //Added hvb @ 11/12/2025
  //const [selectedColumnInfo,setSelectedColumnInfo] = useState<ColumnInfo|null>(null);
  const [filterColumnInfos,setSelectedColumnInfos] = useState<ColumnInfo[]>([]);

  
  const handleLoadFilter = () => {
    if (selectedSavedFilter && savedFilters) {
      const selected = savedFilters.find(f => f.id === selectedSavedFilter);
      if (selected) {
        setFilters(selected.criteria);
      }
    }
  };

  //>>
  const handleGroupAction = (action: "load" | "rename" | "delete" | "update") => {
    switch (action) {
      case "load":
        handleLoadFilter();
        break;
      case "rename":
        //console.log("Rename clicked");
        setOpenedRename(true);
        break;
      case "delete":
        //console.log("Delete clicked");
        setOpenedDelete(true);
        break;
      case "update":
        console.log("Handle update");
        break;
      default:
        console.error(`action handling not defined for ${action}`);
        break;
    }
  };

  const [openedRename, setOpenedRename] = useState(false);
  const [openedDelete, setOpenedDelete] = useState(false);
  const [newName, setNewName] = useState("");

  /*const handleAction = (action: "load" | "rename" | "delete") => {
    if (action === "rename") setOpenedRename(true);
    else if (action === "delete") setOpenedDelete(true);
    else console.log("Load clicked");
  };*/

  const handleRenameSave = () => {
    console.log("Renamed to:", newName);
    setOpenedRename(false);
    setNewName("");
  };

  const handleDeleteConfirm = () => {
    console.log("Deleted confirmed");
    setOpenedDelete(false);
  };

  const loadFilters = async () => {
    setFilterLoading(true);
    const data = await filterManagementServices.getFilters();
    // setFilters(data);
    // const lastUsed = data.find((f: any) => f.last_used);
    // if (lastUsed) setSelectedFilter(lastUsed.id);
    setFilterLoading(false);
  };

  useEffect(()=>{
    console.log("Control mounted load filters");
    loadFilters();
  },[]);

  //<<<

  /*const operatorOptions = [
    { value: '=', label: '=' },
    { value: '>', label: '>' },
    { value: '>=', label: '>=' },
    { value: '<', label: '<' },
    { value: '<=', label: '<=' },
    { value: 'between', label: 'Between' }
  ];*/

  const [operatorOptions, setOperatorOptions] = useState<{ value: string; label: string }[][]>([]);

  const numericOperators = [
    { value: '=', label: '=' },
    { value: '>', label: '>' },
    { value: '>=', label: '>=' },
    { value: '<', label: '<' },
    { value: '<=', label: '<=' },
    { value: '!=', label: 'Not Eqauls'},
    { value: 'between', label: 'Between' },
    { value: 'isNull', label: 'None'},
    { value: 'isNotNull', label: 'Not none'}
  ];

  const stringOperators = [
    { value: '=', label: 'Eqauls' },
    { value: '!=', label: 'Not Eqauls'},
    { value: 'contains', label: 'Contains'},
    { value: 'startsWith', label: 'Starts With'},
    { value: 'endsWith', label: 'Ends With'},
    { value: 'isNull', label: 'None'},
    { value: 'isNotNull', label: 'Not none'}
  ];

  const dateOperators = [
    { value: '=', label: 'Eqauls' },
    { value: '!=', label: 'Not Eqauls'},
    { value: '<', label: 'Before'},
    { value: '<=', label: 'Before or On'},
    { value: '>', label: 'After'},
    { value: '>=', label: 'After or On'},
    { value: 'between', label: 'Between' },
    { value: 'isNull', label: 'None'},
    { value: 'isNotNull', label: 'Not none'}
  ];

  const genOperators = [
    { value: '=', label: '=' },
    { value: '!=', label: 'Not Eqauls'},
    { value: 'isNull', label: 'None'},
    { value: 'isNotNull', label: 'Not none'}
  ];

  const sortDirectionOptions = [
    { value: 'desc', label: 'Descending' },
    { value: 'asc', label: 'Ascending' }
  ];

  const valueFieldOptions = [
    { value: 'principal_os_amt', label: 'Current POS' },
    { value: 'total_amt_disb', label: 'Disbursed Amount' }
  ];

  const setOperatorsForType = (data_type:string,index:number) => {
      if(data_type == "float"){
        if(index == -1)
          setOperatorOptions([...operatorOptions, numericOperators]);
        else if(index>=0){
          operatorOptions[index] = numericOperators;
          setOperatorOptions(operatorOptions);
        }
      }
      else if(data_type == "str"){
        if(index == -1)
        setOperatorOptions([...operatorOptions,stringOperators]);
        else if(index>=0){
          operatorOptions[index] = stringOperators;
          setOperatorOptions(operatorOptions);
        }
      }
      else if(data_type=="date" || data_type=="datetime" || data_type=="time"){
        if(index == -1)
          setOperatorOptions([...operatorOptions,dateOperators]);
        else if(index>=0){
          operatorOptions[index] = dateOperators;
          setOperatorOptions(operatorOptions);
        }
      }else{
        if(index == -1)
          setOperatorOptions([...operatorOptions,genOperators]);
        else if(index>=0){
          operatorOptions[index] = genOperators;
          setOperatorOptions(operatorOptions);
        }
      }
  }

  useEffect(() => {
    if (!initialFilters || initialFilters.length === 0) return;

    const colInfos: ColumnInfo[] = [];
    const ops: { value: string; label: string }[][] = [];

    initialFilters.forEach((filter, index) => {
      const colInfo = availableFields.find(col => col.column_name === filter.field);

      if (colInfo) {
        colInfos.push(colInfo);

        // Assign operator set based on data type
        if (colInfo.data_type === "float") ops.push(numericOperators);
        else if (colInfo.data_type === "str") ops.push(stringOperators);
        else if (["date", "datetime", "time"].includes(colInfo.data_type))
          ops.push(dateOperators);
        else ops.push(genOperators);
      }
    });

    setSelectedColumnInfos(colInfos);
    setOperatorOptions(ops);
  }, [initialFilters, availableFields]);

  const handleAddFilter = () => {
    //setFilters([...filters, { field: availableFields[0].value, operator: '=', value: null, enabled: true }]);
    // const colName = availableFields[0].column_name;
    // setFilters([...filters, { field: colName, operator: '=', value: null, enabled: true }]);
    // let colInfos = availableFields.filter(col=>col.column_name == colName);
    // if(colInfos && colInfos.length > 1){
    //     //HVB @ 12/12/2025
    //     //Set selected columninfo
    //     const colInfo = colInfos[0];
    //     setSelectedColumnInfos([...filterColumnInfos, colInfo]);
    //     setOperatorsForType(colInfo.data_type)
    // }

    const colInfo = availableFields[0];
    const colName = colInfo.column_name;
    setFilters([...filters, { field: colName, operator: '=', value: null, enabled: true }]);
    if(colInfo && colInfo!=null){
        //HVB @ 12/12/2025
        //Set selected columninfo
        setSelectedColumnInfos([...filterColumnInfos, colInfo]);
        setOperatorsForType(colInfo.data_type,-1);
    }
  };

  const handleRemoveFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index));
    setSelectedColumnInfos(filterColumnInfos.filter((_,i)=>i !== index));
    setOperatorOptions(operatorOptions.filter((_,i)=> i !== index));
  };

  

  const handleFilterChange = (index: number, field: keyof FilterCriteria, value: any) => {
    const updatedFilters = [...filters];
    updatedFilters[index] = { ...updatedFilters[index], [field]: value };
    setFilters(updatedFilters);
    
    //Added hvb @ 10/12/2025
    if(field === "field"){
      let columnInfo = availableFields.filter(col=>col.column_name == value);
      if(columnInfo && columnInfo.length > 0){
        const colInfo = columnInfo[0];
        if (colInfo && colInfo != null){
           filterColumnInfos[index] = colInfo;
           setSelectedColumnInfos(filterColumnInfos);
          let data_type = colInfo.data_type;    
          setOperatorsForType(data_type,index);
        }
      }
    }
  }

  

  const handleApply = () => {
    onApply(filters, target);
    //Commented hvb @ 26/10/2025
    //Even though there is error this closes, anyway
    //We handle closing from apply filter page, rather than here.
    //onClose();
  };

  const handleSaveFilter = () => {
    if (newFilterName && onSaveFilter) {
      setIsSaving(true);
      onSaveFilter(newFilterName, filters);

      /*const newSavedFilter = {
      id: `filter-${Date.now()}`,
      name,
      criteria
    };
    
    setSavedFilters([...savedFilters, newSavedFilter]);*/

      //Update in backend as well via api
      setNewFilterName('');
      setIsSaving(false);
    }
  };

  const handleClearAll = () => {
    //setFilters([{ field: availableFields[0].value, operator: '=', value: null, enabled: true }]);
    //Mod hvb @ 12/12/2025
    //setFilters([{ field: availableFields[0].column_name, operator: '=', value: null, enabled: true }]);
    setFilters([]);
    setSelectedColumnInfos([]);
    setOperatorOptions([]);

  };

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title="🔍 Apply Selection Criteria" 
      size="lg"
    >
      <Stack gap="md">
        <Text fw={500}>Filters:</Text>
        
        {filters.map((filter, index) => (
          <Group key={index} wrap="nowrap" align="center">
            <Checkbox
              checked={filter.enabled}
              onChange={(e) => handleFilterChange(index, 'enabled', e.currentTarget.checked)}
            />
            
            {/* <Select
              //data={availableFields.map(e=>e.column_name)}
              data={availableFields.map(e=> ({label:e.column_name,value:e.column_name}))}
              value={filter.field}
              onChange={(value) => handleFilterChange(index, 'field', value)}
              style={{ width: '140px' }}
            /> */}

            <VirtualizedSearchableSelect
              data={availableFields.map(e=> e.column_name)}
              value={filter.field}
              onChange={(value) => handleFilterChange(index, 'field', value)}
              style={{ width: '140px' }}
            />
            
            <Select
              data={index <= operatorOptions.length-1 ? operatorOptions[index] : genOperators}
              value={filter.operator}
              onChange={(value) => handleFilterChange(index, 'operator', value)}
              style={{ width: '100px' }}
            />
            
            {/* Replaced with new values component hvb @ 11/12/2025 */}
            {/* {filter.operator === 'between' ? (
              <Group wrap="nowrap">
                <NumberInput
                  value={filter.min_value || undefined}
                  onChange={(value) => handleFilterChange(index, 'min_value', value)}
                  style={{ width: '100px' }}
                  placeholder="Min"
                />
                <Text>to</Text>
                <NumberInput
                  value={filter.max_value || undefined}
                  onChange={(value) => handleFilterChange(index, 'max_value', value)}
                  style={{ width: '100px' }}
                  placeholder="Max"
                />
              </Group>
            ) : filter.field === 'state' ? (
              <Select
                data={[
                  { value: 'Maharashtra', label: 'Maharashtra' },
                  { value: 'Gujarat', label: 'Gujarat' },
                  { value: 'Karnataka', label: 'Karnataka' }
                ]}
                value={filter.value?.toString() || ''}
                onChange={(value) => handleFilterChange(index, 'value', value)}
                style={{ width: '180px' }}
              />
            ) : 
             filter.operator === "isNotNull" || filter.operator === "isNull" ? 
             (<TextInput readOnly />) : 
            (
              <NumberInput
                value={typeof filter.value === 'number' ? filter.value : undefined}
                onChange={(value) => handleFilterChange(index, 'value', value)}
                style={{ width: '180px' }}
              />
            )} */}
            
            <FilterValuesDropdown 
              dataSetId={datasetId == null?undefined:(datasetId as string)}
              filterField={index <= filterColumnInfos.length-1?filterColumnInfos[index]:null}
              index={index}
              onFilterValueChange={handleFilterChange}
              operatorValue={filter.operator}
              value1={(filter.value??filter.min_value)??undefined}
              value2={filter.max_value??undefined}
            />

            <CloseButton
              onClick={() => handleRemoveFilter(index)}
              title="Remove filter"
            />
          </Group>
        ))}
        
        <Button 
          leftSection={<IconPlus size="1rem" />}
          variant="outline" 
          onClick={handleAddFilter}
          fullWidth={false}
          style={{ alignSelf: 'flex-start' }}
        >
          Add Filter
        </Button>

        <Box mt="md">
          <Text fw={500}>🎯 Target Sub-Pool Selection</Text>
          
          <Group mt="sm" align="center">
            <Text size="sm" w={120}>Max Pool Value:</Text>
            <NumberInput
              value={target.maxPoolValue}
              onChange={(value) => setTarget({ ...target, maxPoolValue: typeof value === 'number' ? value : 0 })}
              leftSection="₹"
              style={{ width: '200px' }}
            />
            <Text size="xs" c="dimmed">(Cumulative selection cap)</Text>
          </Group>
          
          <Group mt="sm" align="center">
            <Text size="sm" w={120}>Sort Records By:</Text>
            <Select
              // data={availableFields}
              data={availableFields.map(e=> ({label:e.column_name,value:e.column_name}))}
              value={target.sortField}
              onChange={(value) => setTarget({ ...target, sortField: value || 'collection_12m' })}
              style={{ width: '150px' }}
            />
            <Select
              data={sortDirectionOptions}
              value={target.sortDirection}
              onChange={(value) => setTarget({ ...target, sortDirection: value as 'asc' | 'desc' || 'desc' })}
              style={{ width: '120px' }}
            />
          </Group>
          
          <Group mt="sm" align="center">
            <Text size="sm" w={120}>Sum Value From:</Text>
            <Select
              data={valueFieldOptions}
              value={target.sumValueField}
              onChange={(value) => setTarget({ ...target, sumValueField: value || 'principal_os_amt' })}
              style={{ width: '150px' }}
            />
            <Text size="xs" c="dimmed">(Used for cumulative sum)</Text>
          </Group>
        </Box>

        {savedFilters && savedFilters.length > 0 && (
          <Group mt="md" align='center' gap="xs">
            <Select
              label="Load saved filter"
              data={savedFilters.map(f => ({ value: f.id, label: f.name }))}
              value={selectedSavedFilter}
              onChange={setSelectedSavedFilter}
              style={{ width: '200px' }}
            />
            <Button 
              onClick={handleLoadFilter} 
              disabled={!selectedSavedFilter}
              variant="outline"
              mt={25}
            >
              Load
            </Button>
            <FitlerSaveActions onAction={handleGroupAction}/>
          </Group>
        )}

        {onSaveFilter && (
          <Group mt="md">
            <TextInput 
              label="Save current filter as"
              value={newFilterName}
              onChange={(e) => setNewFilterName(e.currentTarget.value)}
              style={{ width: '200px' }}
            />
            <Button 
              onClick={handleSaveFilter} 
              loading={isSaving}
              disabled={!newFilterName}
              variant="outline"
              mt={25}
            >
              Save
            </Button>
          </Group>
        )}

        {/* Rename Modal */}
        <Modal
          opened={openedRename}
          onClose={() => setOpenedRename(false)}
          title="Rename Filter"
          centered
        >
          <TextInput
            label="New name"
            placeholder="Enter new name"
            value={newName}
            onChange={(e) => setNewName(e.currentTarget.value)}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setOpenedRename(false)}>
              Cancel
            </Button>
            <Button color="blue" onClick={handleRenameSave}>
              Save
            </Button>
          </Group>
        </Modal>

        {/* Delete Confirmation Modal */}
        <Modal
          opened={openedDelete}
          onClose={() => setOpenedDelete(false)}
          title="Confirm Delete"
          centered
        >
          <Text>Are you sure you want to delete this filter?</Text>
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setOpenedDelete(false)}>
              No
            </Button>
            <Button color="red" onClick={handleDeleteConfirm}>
              Yes, Delete
            </Button>
          </Group>
        </Modal>

        <Group justify="space-between" mt="lg">
          <Button variant="light" leftSection={<IconX size="1rem" />} onClick={handleClearAll}>Clear All</Button>
          <Group>
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button leftSection={<IconCheck size="1rem" />} onClick={handleApply}>Apply Filters</Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  );
};
