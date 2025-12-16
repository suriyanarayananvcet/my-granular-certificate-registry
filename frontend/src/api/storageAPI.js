import baseAPI from "./baseAPI";

export const getStorageRecordsAPI = (device_ids) => {
    // Pass list of IDs as query params: ?storage_record_ids=1&storage_record_ids=2
    const params = new URLSearchParams();
    device_ids.forEach(id => params.append("storage_record_ids", id));
    return baseAPI.get(`/storage/storage_records`, { params });
};

export const getAllocatedStorageRecordsAPI = (device_id) => {
    return baseAPI.get(`/storage/allocated_storage_records/${device_id}`);
};
