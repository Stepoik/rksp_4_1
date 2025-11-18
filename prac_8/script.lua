function set_user_header(req)
    req:headers("user-id", req:params("Resp0_user_id"))
end