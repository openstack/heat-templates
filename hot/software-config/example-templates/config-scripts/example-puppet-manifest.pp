file { 'barfile':
    ensure  => file,
    mode    => '0644',
    path    => "/tmp/$::bar",
    content => "$::foo",
}

file { 'output_result':
    ensure  => file,
    path    => "$::heat_outputs_path.result",
    mode    => '0644',
    content => "The file /tmp/$::bar contains $::foo",
}
