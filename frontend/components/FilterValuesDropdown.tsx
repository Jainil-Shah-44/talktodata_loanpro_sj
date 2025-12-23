import { useFieldState } from "@/hooks/useFieldState";
import { FilterCriteria } from "@/src/types";
import { ColumnInfo } from "@/src/types/mappings";
import { Group, Loader, NumberInput, Skeleton, Text, TextInput } from "@mantine/core";
import { DateInput } from '@mantine/dates';
import { notifications } from "@mantine/notifications";
import { useEffect } from "react";
import { CreatableSelect } from "./CreatableSelect";

interface FilterValuesDropDownProps{
    dataSetId:string|undefined,
    filterField:ColumnInfo|null,
    operatorValue:string,
    index:number,
    value1:number|string|undefined,
    value2:number|string|undefined,
    onFilterValueChange: (index: number, field: keyof FilterCriteria, value: any) => void;
}

export default function FilterValuesDropdown({dataSetId,filterField,operatorValue,index,value1,value2,onFilterValueChange}:FilterValuesDropDownProps) {
    const loadingSkeleton = <Group wrap="nowrap">
            <Skeleton height={32} width={110} radius="md" animate /> {/* dropdown shimmer */}

            {/* Loader under skeleton to emphasize loading */}
            <div style={{ marginTop: 4, display: "flex", justifyContent: "center" }}>
                <Loader size={20} />
            </div>
        </Group>;
        

    if(filterField == null || dataSetId == undefined)
        return loadingSkeleton;

    const request = {
        pk_id: dataSetId,
        column_name: filterField.column_name,
        column_type: filterField.data_type,
        is_json_column: filterField.is_json_col,
    };

    const { data, isPending, error } = useFieldState(request);
    const data_type = filterField.data_type;

    // 🔥 Show error as notification instead of inline UI
    useEffect(() => {
        if (error) {
        notifications.show({
            title: "Error loading field stats",
            message: error.message || "Unknown error",
            color: "red",
        });
        }
    }, [error]);

    // ⭐ CASE 1: LOADING STATE → Skeleton + Loader + disabled Select
    if (isPending) {
        return loadingSkeleton;
    }

    const min_field_val = (error || data == undefined || data?.type === "distinct")?undefined:data.min;
    const max_field_val = (error || data == undefined || data?.type === "distinct")?undefined:data.max;
    // const options =
    //     data?.type === "distinct"
    //     ? data.values?.map((v) => ({ value: v, label: v })) ?? []
    //   : [];
    const options =
        data?.type === "distinct"
        ? data.values ?? []
      : [];

    // ⭐ CASE 2: ERROR → Disabled dropdown (notification already shown)
    //if (error || data == undefined) {
        if(data_type == "float"){
            if(operatorValue === "between"){
                return(
                <Group wrap="nowrap">
                    <NumberInput
                    value={value1}
                    onChange={(value) => onFilterValueChange(index, 'min_value', value)}
                    style={{ width: '100px' }}
                    placeholder="Min"
                    min={typeof min_field_val === "number" ? min_field_val : undefined}
                    max={typeof max_field_val === "number" ? max_field_val : undefined}
                    />
                    <Text>to</Text>
                    <NumberInput
                    value={value2}
                    onChange={(value) => onFilterValueChange(index, 'max_value', value)}
                    style={{ width: '100px' }}
                    placeholder="Max"
                    min={typeof min_field_val === "number" ? min_field_val : undefined}
                    max={typeof max_field_val === "number" ? max_field_val : undefined}
                    />
                </Group>);
            }else if(operatorValue === "isNull" || operatorValue === "isNotNull"){
                return(
                    <NumberInput readOnly />
                )
            }else{
                return(
                    <NumberInput value={typeof value1 === 'number' ? value1 : undefined}
                    onChange={(value) => onFilterValueChange(index, 'value', value)}
                    min={typeof min_field_val === "number" ? min_field_val : undefined}
                    max={typeof max_field_val === "number" ? max_field_val : undefined}
                    style={{ width: '180px' }} />
                )
            }
        } 
        else if(data_type=="date" || data_type=="datetime" || data_type=="time"){
            if(operatorValue === "between"){
                return(
                <Group wrap="nowrap">
                    <DateInput
                        clearable
                        value={typeof value1 === "string" ? new Date(value1) : undefined}
                        onChange={(value) => onFilterValueChange(index, 'min_value', value)}
                        label="From date"
                        placeholder="From date"
                        style={{ width: '100px' }}
                        minDate={typeof min_field_val === "string" ? new Date(min_field_val) : undefined}
                        maxDate={typeof max_field_val === "string" ? new Date(max_field_val) : undefined}
                    />
                    <Text>to</Text>
                    <DateInput
                        clearable
                        value={typeof value2 === "string" ? new Date(value2) : undefined}
                        onChange={(value) => onFilterValueChange(index, 'max_value', value)}
                        label="Till date"
                        placeholder="Till date"
                        style={{ width: '100px' }}
                        minDate={typeof min_field_val === "string" ? new Date(min_field_val) : undefined}
                        maxDate={typeof max_field_val === "string" ? new Date(max_field_val) : undefined}
                    />
                </Group>);
            }else if(operatorValue === "isNull" || operatorValue === "isNotNull"){
                return(
                    <DateInput disabled />
                )
            }else{
                return(
                    <DateInput
                        clearable
                        value={typeof value1 === "string" ? new Date(value1) : undefined}
                        onChange={(value) => onFilterValueChange(index, 'value', value)}
                        label="From date"
                        placeholder="From date"
                        style={{ width: '100px' }}
                        minDate={typeof min_field_val === "string" ? new Date(min_field_val) : undefined}
                        maxDate={typeof max_field_val === "string" ? new Date(max_field_val) : undefined}
                    />
                )
            }
        }
        else if(data_type === "str"){
            return(
            <CreatableSelect
              label={""}
              required
              // data={["PDF", "Excel", "CSV"]}
              data={options}
              value={typeof value1 === "string" ? value1 : undefined}
              onChange={(value) => onFilterValueChange(index, 'value', value)}
              isAddOption={false}
            />
        )
        }
        else {
            //generic type
            return(
                    <TextInput value={typeof value1 === 'string' ? value1 : undefined}
                    onChange={(value) => onFilterValueChange(index, 'value', value)}
                    style={{ width: '180px' }} />
                )
        }
    //}

     

    // ⭐ CASE 3: SUCCESS → Normal dropdown
    // return (
    //     <Select
    //     label="Field Stats"
    //     placeholder="Select value"
    //     data={options}
    //     disabled={false}
    //     comboboxProps={{ withinPortal: false }}
    //     nothingFound="No values"
    //     />
    // );
}
