using Test
using RNCAnalytics

@testset "summarize edge cases" begin
    # Temporarily point to a non-existing db to simulate empty/absent table
    old = get(ENV, "IPPEL_DB", nothing)
    try
        ENV["IPPEL_DB"] = "g:/path/that/does/not/exist/ippel_system.db"
        s = RNCAnalytics.summarize()
        @test s.total >= 0
        @test s.pending >= 0
        @test s.finalized >= 0
        @test :month in names(s.by_month) && :count in names(s.by_month)
    finally
        if old === nothing
            delete!(ENV, "IPPEL_DB")
        else
            ENV["IPPEL_DB"] = old
        end
    end
end
