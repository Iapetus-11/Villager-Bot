# Get the replica ID (1-N) of the currently running Villager Bot docker compose service
echo "$( v="$( nslookup "$( hostname -i )" | head -n 1 )"; v="${v##* = }"; v="${v%%.*}"; v="${v##*-}"; v="${v##*_}"; echo "$v" )"
