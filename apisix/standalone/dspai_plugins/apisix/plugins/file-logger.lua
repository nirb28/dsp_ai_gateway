-- Introduce the module we need in the header
local log_util     =   require("apisix.utils.log-util")
local core         =   require("apisix.core")
local plugin       =   require("apisix.plugin")
local ngx          =   ngx

-- Declare the plugin's name
local plugin_name = "file-logger"

-- Define the plugin schema format
local schema = {
    type = "object",
    properties = {
        path = {
            type = "string"
        },
    },
    required = {"path"}
}

-- Plugin metadata schema
local metadata_schema = {
    type = "object",
    properties = {
        log_format = log_util.metadata_schema_log_format
    }
}

local _M = {
    version = 0.1,
    priority = 399,
    name = plugin_name,
    schema = schema,
    metadata_schema = metadata_schema
}

-- Check if the plugin configuration is correct
function _M.check_schema(conf, schema_type)
    if schema_type == core.schema.TYPE_METADATA then
        return core.schema.check(metadata_schema, conf)
    end
    return core.schema.check(schema, conf)
end

-- Log phase

local function write_file_data(conf, log_message)
    local msg, err = core.json.encode(log_message)
    if err then
        return core.log.error("message json serialization failed, error info : ", err)
    end

    local file, err = io.open(conf.path, 'a+')

    if not file then
        core.log.error("failed to open file: ", conf.path, ", error info: ", err)
    else
        local ok, err = file:write(msg, '\n')
        if not ok then
            core.log.error("failed to write file: ", conf.path, ", error info: ", err)
        else
            file:flush()
        end
        file:close()
    end
end

function _M.log(conf, ctx)
    local metadata = plugin.plugin_metadata(plugin_name)
    local entry

    if metadata and metadata.value.log_format
        and core.table.nkeys(metadata.value.log_format) > 0
    then
        entry = log_util.get_custom_format_log(ctx, metadata.value.log_format)
    else
        entry = log_util.get_full_log(ngx, conf)
    end

    write_file_data(conf, entry)
end

return _M