def cauchy_lower_li(x)
	if(x<2)
		return 1
	end
	if(x<4)
		return 2
	
	ret =0
	while ((x/2) < 4)
		y = x/2
		lg = Math.log(y,2)
		ret += (x-y)*lg
		x=y
	end
	return x
end


puts cauchy_lower_li(200)