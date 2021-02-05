connection: "my-connection"

include: "/views/*.view.lkml"                # include all views in the views/ folder in this project

explore: user_events_cube {
  hidden: no

  join: dummy_view {
    view_label: "Dummy"
    type: left_outer
    relationship: one_to_one
    sql_on: ${user_events_cube.some_id} = ${dummy_view.some_id} ;;
  }
  
}

explore: user_search_cube {
  hidden: no
}
